/**
 * Offline Support Module
 *
 * Provides offline capabilities including:
 * - Network state detection
 * - Request queueing when offline
 * - Optimistic updates
 * - Cache persistence
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo, { NetInfoState, NetInfoSubscription } from '@react-native-community/netinfo';

// Types
export interface QueuedRequest {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  url: string;
  data?: any;
  headers?: Record<string, string>;
  timestamp: number;
  retryCount: number;
  priority: number;
  onSuccess?: string; // Event name to emit on success
  onError?: string;   // Event name to emit on error
}

export interface OfflineState {
  isOnline: boolean;
  isConnected: boolean;
  connectionType: string | null;
  lastOnlineAt: number | null;
  queueSize: number;
}

export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  expiresAt: number;
  etag?: string;
}

// Storage keys
const STORAGE_KEYS = {
  QUEUE: '@idkit:offline_queue',
  CACHE: '@idkit:cache',
  STATE: '@idkit:offline_state',
  PENDING_ACTIONS: '@idkit:pending_actions',
};

// Default cache duration (5 minutes)
const DEFAULT_CACHE_DURATION = 5 * 60 * 1000;

// Maximum queue size
const MAX_QUEUE_SIZE = 100;

// Maximum retry count
const MAX_RETRY_COUNT = 3;

// Event emitter for offline events
type EventCallback = (...args: any[]) => void;
const eventListeners: Map<string, Set<EventCallback>> = new Map();

function emit(event: string, ...args: any[]) {
  const listeners = eventListeners.get(event);
  if (listeners) {
    listeners.forEach(callback => callback(...args));
  }
}

function on(event: string, callback: EventCallback): () => void {
  if (!eventListeners.has(event)) {
    eventListeners.set(event, new Set());
  }
  eventListeners.get(event)!.add(callback);

  // Return unsubscribe function
  return () => {
    eventListeners.get(event)?.delete(callback);
  };
}

/**
 * Offline Queue Manager
 *
 * Manages queued requests when the app is offline.
 */
class OfflineQueue {
  private queue: QueuedRequest[] = [];
  private isProcessing = false;

  async initialize(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEYS.QUEUE);
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
      this.queue = [];
    }
  }

  async add(request: Omit<QueuedRequest, 'id' | 'timestamp' | 'retryCount'>): Promise<string> {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const queuedRequest: QueuedRequest = {
      ...request,
      id,
      timestamp: Date.now(),
      retryCount: 0,
      priority: request.priority ?? 0,
    };

    // Enforce queue size limit
    if (this.queue.length >= MAX_QUEUE_SIZE) {
      // Remove oldest low-priority items
      this.queue.sort((a, b) => b.priority - a.priority || a.timestamp - b.timestamp);
      this.queue = this.queue.slice(0, MAX_QUEUE_SIZE - 1);
    }

    this.queue.push(queuedRequest);
    this.queue.sort((a, b) => b.priority - a.priority || a.timestamp - b.timestamp);

    await this.persist();
    emit('queue:added', queuedRequest);

    return id;
  }

  async remove(id: string): Promise<boolean> {
    const index = this.queue.findIndex(r => r.id === id);
    if (index === -1) return false;

    this.queue.splice(index, 1);
    await this.persist();
    emit('queue:removed', id);

    return true;
  }

  async clear(): Promise<void> {
    this.queue = [];
    await this.persist();
    emit('queue:cleared');
  }

  getQueue(): QueuedRequest[] {
    return [...this.queue];
  }

  getSize(): number {
    return this.queue.length;
  }

  async process(
    executor: (request: QueuedRequest) => Promise<any>
  ): Promise<{ success: number; failed: number }> {
    if (this.isProcessing || this.queue.length === 0) {
      return { success: 0, failed: 0 };
    }

    this.isProcessing = true;
    let success = 0;
    let failed = 0;

    emit('queue:processing:start');

    try {
      const toProcess = [...this.queue];

      for (const request of toProcess) {
        try {
          const result = await executor(request);
          await this.remove(request.id);
          success++;

          if (request.onSuccess) {
            emit(request.onSuccess, { request, result });
          }
          emit('queue:item:success', { request, result });
        } catch (error) {
          request.retryCount++;

          if (request.retryCount >= MAX_RETRY_COUNT) {
            await this.remove(request.id);
            failed++;

            if (request.onError) {
              emit(request.onError, { request, error });
            }
            emit('queue:item:failed', { request, error });
          } else {
            // Keep in queue for retry
            await this.persist();
            emit('queue:item:retry', { request, retryCount: request.retryCount });
          }
        }
      }
    } finally {
      this.isProcessing = false;
      emit('queue:processing:complete', { success, failed });
    }

    return { success, failed };
  }

  private async persist(): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.QUEUE, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to persist offline queue:', error);
    }
  }
}

/**
 * Cache Manager
 *
 * Manages data caching with expiration.
 */
class CacheManager {
  private cache: Map<string, CacheEntry> = new Map();
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEYS.CACHE);
      if (stored) {
        const entries: [string, CacheEntry][] = JSON.parse(stored);
        const now = Date.now();

        // Only load non-expired entries
        entries.forEach(([key, entry]) => {
          if (entry.expiresAt > now) {
            this.cache.set(key, entry);
          }
        });
      }
      this.initialized = true;
    } catch (error) {
      console.error('Failed to load cache:', error);
    }
  }

  async set<T>(
    key: string,
    data: T,
    options: { duration?: number; etag?: string } = {}
  ): Promise<void> {
    const duration = options.duration ?? DEFAULT_CACHE_DURATION;
    const now = Date.now();

    const entry: CacheEntry<T> = {
      data,
      timestamp: now,
      expiresAt: now + duration,
      etag: options.etag,
    };

    this.cache.set(key, entry);
    await this.persist();
    emit('cache:set', { key, entry });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;

    if (!entry) return null;

    // Check expiration
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  getWithMeta<T>(key: string): CacheEntry<T> | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;

    if (!entry) return null;

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry;
  }

  async delete(key: string): Promise<boolean> {
    const deleted = this.cache.delete(key);
    if (deleted) {
      await this.persist();
      emit('cache:delete', key);
    }
    return deleted;
  }

  async clear(): Promise<void> {
    this.cache.clear();
    await this.persist();
    emit('cache:cleared');
  }

  async prune(): Promise<number> {
    const now = Date.now();
    let pruned = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
        pruned++;
      }
    }

    if (pruned > 0) {
      await this.persist();
      emit('cache:pruned', pruned);
    }

    return pruned;
  }

  getSize(): number {
    return this.cache.size;
  }

  getKeys(): string[] {
    return Array.from(this.cache.keys());
  }

  private async persist(): Promise<void> {
    try {
      const entries = Array.from(this.cache.entries());
      await AsyncStorage.setItem(STORAGE_KEYS.CACHE, JSON.stringify(entries));
    } catch (error) {
      console.error('Failed to persist cache:', error);
    }
  }
}

/**
 * Network Monitor
 *
 * Monitors network connectivity and triggers sync when online.
 */
class NetworkMonitor {
  private state: OfflineState = {
    isOnline: true,
    isConnected: true,
    connectionType: null,
    lastOnlineAt: Date.now(),
    queueSize: 0,
  };
  private subscription: NetInfoSubscription | null = null;
  private onOnlineCallbacks: Set<() => void> = new Set();

  async initialize(): Promise<void> {
    // Get initial state
    const netState = await NetInfo.fetch();
    this.updateState(netState);

    // Subscribe to changes
    this.subscription = NetInfo.addEventListener(state => {
      const wasOnline = this.state.isOnline;
      this.updateState(state);

      if (!wasOnline && this.state.isOnline) {
        emit('network:online');
        this.onOnlineCallbacks.forEach(cb => cb());
      } else if (wasOnline && !this.state.isOnline) {
        emit('network:offline');
      }
    });
  }

  private updateState(netState: NetInfoState): void {
    const isOnline = netState.isConnected === true && netState.isInternetReachable !== false;

    this.state = {
      isOnline,
      isConnected: netState.isConnected ?? false,
      connectionType: netState.type,
      lastOnlineAt: isOnline ? Date.now() : this.state.lastOnlineAt,
      queueSize: offlineQueue.getSize(),
    };

    emit('network:state', this.state);
  }

  getState(): OfflineState {
    return { ...this.state };
  }

  isOnline(): boolean {
    return this.state.isOnline;
  }

  onOnline(callback: () => void): () => void {
    this.onOnlineCallbacks.add(callback);
    return () => this.onOnlineCallbacks.delete(callback);
  }

  destroy(): void {
    if (this.subscription) {
      this.subscription();
      this.subscription = null;
    }
    this.onOnlineCallbacks.clear();
  }
}

// Create singletons
const offlineQueue = new OfflineQueue();
const cacheManager = new CacheManager();
const networkMonitor = new NetworkMonitor();

/**
 * Initialize offline support
 *
 * Call this at app startup.
 */
export async function initializeOfflineSupport(): Promise<void> {
  await Promise.all([
    offlineQueue.initialize(),
    cacheManager.initialize(),
    networkMonitor.initialize(),
  ]);

  // Set up auto-sync when coming online
  networkMonitor.onOnline(async () => {
    console.log('Network online, processing queue...');
    await syncOfflineQueue();
  });

  // Prune expired cache entries
  await cacheManager.prune();

  emit('offline:initialized');
}

/**
 * Queue a request for offline execution
 */
export async function queueRequest(
  request: Omit<QueuedRequest, 'id' | 'timestamp' | 'retryCount'>
): Promise<string> {
  return offlineQueue.add(request);
}

/**
 * Process the offline queue
 */
export async function syncOfflineQueue(): Promise<{ success: number; failed: number }> {
  const { api } = await import('./api');

  return offlineQueue.process(async (request) => {
    switch (request.method) {
      case 'GET':
        return api.get(request.url);
      case 'POST':
        return api.post(request.url, request.data);
      case 'PUT':
        return api.put(request.url, request.data);
      case 'PATCH':
        return api.patch(request.url, request.data);
      case 'DELETE':
        return api.delete(request.url);
      default:
        throw new Error(`Unknown method: ${request.method}`);
    }
  });
}

/**
 * Get cached data or fetch from API
 */
export async function getCachedOrFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: { duration?: number; forceRefresh?: boolean } = {}
): Promise<T> {
  // Try cache first (unless forcing refresh)
  if (!options.forceRefresh) {
    const cached = cacheManager.get<T>(key);
    if (cached !== null) {
      return cached;
    }
  }

  // If offline, return cached (even if expired) or throw
  if (!networkMonitor.isOnline()) {
    const cached = cacheManager.get<T>(key);
    if (cached !== null) {
      return cached;
    }
    throw new Error('No cached data available and device is offline');
  }

  // Fetch fresh data
  try {
    const data = await fetcher();
    await cacheManager.set(key, data, { duration: options.duration });
    return data;
  } catch (error) {
    // On error, try to return stale cache
    const cached = cacheManager.get<T>(key);
    if (cached !== null) {
      return cached;
    }
    throw error;
  }
}

/**
 * Optimistic update helper
 *
 * Updates cache immediately, queues request, and rolls back on failure.
 */
export async function optimisticUpdate<T>(
  cacheKey: string,
  updateFn: (current: T | null) => T,
  request: Omit<QueuedRequest, 'id' | 'timestamp' | 'retryCount'>,
  options: { revertOnFailure?: boolean } = {}
): Promise<string> {
  const current = cacheManager.get<T>(cacheKey);
  const updated = updateFn(current);

  // Update cache immediately
  await cacheManager.set(cacheKey, updated);

  // Queue the request
  const requestId = await queueRequest({
    ...request,
    onError: options.revertOnFailure !== false ? 'optimistic:revert' : undefined,
  });

  // Set up revert listener if needed
  if (options.revertOnFailure !== false && current !== null) {
    const unsubscribe = on('optimistic:revert', ({ request: failedRequest }) => {
      if (failedRequest.id === requestId) {
        cacheManager.set(cacheKey, current);
        unsubscribe();
      }
    });
  }

  return requestId;
}

// Export utilities
export const offlineSupport = {
  // Core functions
  initialize: initializeOfflineSupport,
  queueRequest,
  syncQueue: syncOfflineQueue,
  getCachedOrFetch,
  optimisticUpdate,

  // Queue access
  getQueue: () => offlineQueue.getQueue(),
  getQueueSize: () => offlineQueue.getSize(),
  clearQueue: () => offlineQueue.clear(),

  // Cache access
  getCache: <T>(key: string) => cacheManager.get<T>(key),
  setCache: <T>(key: string, data: T, duration?: number) =>
    cacheManager.set(key, data, { duration }),
  deleteCache: (key: string) => cacheManager.delete(key),
  clearCache: () => cacheManager.clear(),
  getCacheKeys: () => cacheManager.getKeys(),
  pruneCache: () => cacheManager.prune(),

  // Network state
  getNetworkState: () => networkMonitor.getState(),
  isOnline: () => networkMonitor.isOnline(),
  onOnline: (callback: () => void) => networkMonitor.onOnline(callback),

  // Events
  on,
  emit,
};

export default offlineSupport;
