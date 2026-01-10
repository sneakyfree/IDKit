/**
 * Background Sync Service
 *
 * Handles background synchronization of data when the app
 * comes back online or enters the foreground.
 */

import { AppState, AppStateStatus } from 'react-native';
import { offlineSupport, OfflineState } from './offline';

// Types
export interface SyncConfig {
  // How often to check for sync (ms)
  syncInterval: number;
  // Minimum time between syncs (ms)
  minSyncGap: number;
  // Whether to sync on app foreground
  syncOnForeground: boolean;
  // Whether to sync when network becomes available
  syncOnConnect: boolean;
  // Priority sync items (always sync first)
  priorityItems: string[];
}

export interface SyncResult {
  success: boolean;
  timestamp: number;
  queueProcessed: { success: number; failed: number };
  dataRefreshed: string[];
  errors: string[];
}

export interface SyncTask {
  key: string;
  name: string;
  priority: number;
  lastSync: number | null;
  syncFn: () => Promise<void>;
  shouldSync?: (state: OfflineState) => boolean;
}

// Default configuration
const DEFAULT_CONFIG: SyncConfig = {
  syncInterval: 5 * 60 * 1000, // 5 minutes
  minSyncGap: 30 * 1000, // 30 seconds
  syncOnForeground: true,
  syncOnConnect: true,
  priorityItems: ['feed', 'inbox', 'profile'],
};

/**
 * Background Sync Manager
 */
class SyncManager {
  private config: SyncConfig;
  private tasks: Map<string, SyncTask> = new Map();
  private lastSyncTime: number = 0;
  private isSyncing: boolean = false;
  private syncInterval: NodeJS.Timer | null = null;
  private appStateSubscription: any = null;
  private networkSubscription: (() => void) | null = null;

  constructor(config: Partial<SyncConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Initialize the sync manager
   */
  async initialize(): Promise<void> {
    // Listen for app state changes
    if (this.config.syncOnForeground) {
      this.appStateSubscription = AppState.addEventListener(
        'change',
        this.handleAppStateChange.bind(this)
      );
    }

    // Listen for network changes
    if (this.config.syncOnConnect) {
      this.networkSubscription = offlineSupport.onOnline(() => {
        this.sync('network_online');
      });
    }

    // Start periodic sync
    if (this.config.syncInterval > 0) {
      this.syncInterval = setInterval(() => {
        if (offlineSupport.isOnline()) {
          this.sync('interval');
        }
      }, this.config.syncInterval);
    }

    // Register default sync tasks
    this.registerDefaultTasks();

    console.log('SyncManager initialized');
  }

  /**
   * Stop the sync manager
   */
  destroy(): void {
    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    if (this.networkSubscription) {
      this.networkSubscription();
      this.networkSubscription = null;
    }

    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    this.tasks.clear();
    console.log('SyncManager destroyed');
  }

  /**
   * Register a sync task
   */
  registerTask(task: SyncTask): void {
    this.tasks.set(task.key, task);
  }

  /**
   * Unregister a sync task
   */
  unregisterTask(key: string): boolean {
    return this.tasks.delete(key);
  }

  /**
   * Trigger a sync
   */
  async sync(trigger: string = 'manual'): Promise<SyncResult> {
    // Check if we should sync
    if (this.isSyncing) {
      return {
        success: false,
        timestamp: Date.now(),
        queueProcessed: { success: 0, failed: 0 },
        dataRefreshed: [],
        errors: ['Sync already in progress'],
      };
    }

    const now = Date.now();
    if (now - this.lastSyncTime < this.config.minSyncGap) {
      return {
        success: false,
        timestamp: now,
        queueProcessed: { success: 0, failed: 0 },
        dataRefreshed: [],
        errors: ['Sync throttled'],
      };
    }

    if (!offlineSupport.isOnline()) {
      return {
        success: false,
        timestamp: now,
        queueProcessed: { success: 0, failed: 0 },
        dataRefreshed: [],
        errors: ['Device is offline'],
      };
    }

    this.isSyncing = true;
    this.lastSyncTime = now;

    const result: SyncResult = {
      success: true,
      timestamp: now,
      queueProcessed: { success: 0, failed: 0 },
      dataRefreshed: [],
      errors: [],
    };

    offlineSupport.emit('sync:start', { trigger });

    try {
      // 1. Process offline queue first
      result.queueProcessed = await offlineSupport.syncQueue();

      // 2. Run sync tasks
      const networkState = offlineSupport.getNetworkState();
      const sortedTasks = this.getSortedTasks();

      for (const task of sortedTasks) {
        // Check if task should sync
        if (task.shouldSync && !task.shouldSync(networkState)) {
          continue;
        }

        try {
          await task.syncFn();
          task.lastSync = Date.now();
          result.dataRefreshed.push(task.key);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          result.errors.push(`${task.key}: ${errorMessage}`);
        }
      }

      result.success = result.errors.length === 0;
    } catch (error) {
      result.success = false;
      result.errors.push(error instanceof Error ? error.message : String(error));
    } finally {
      this.isSyncing = false;
      offlineSupport.emit('sync:complete', result);
    }

    return result;
  }

  /**
   * Sync a specific task
   */
  async syncTask(key: string): Promise<boolean> {
    const task = this.tasks.get(key);
    if (!task) {
      return false;
    }

    if (!offlineSupport.isOnline()) {
      return false;
    }

    try {
      await task.syncFn();
      task.lastSync = Date.now();
      return true;
    } catch (error) {
      console.error(`Sync task ${key} failed:`, error);
      return false;
    }
  }

  /**
   * Get sync status
   */
  getStatus(): {
    isSyncing: boolean;
    lastSyncTime: number;
    tasks: Array<{ key: string; name: string; lastSync: number | null }>;
    queueSize: number;
  } {
    return {
      isSyncing: this.isSyncing,
      lastSyncTime: this.lastSyncTime,
      tasks: Array.from(this.tasks.values()).map(t => ({
        key: t.key,
        name: t.name,
        lastSync: t.lastSync,
      })),
      queueSize: offlineSupport.getQueueSize(),
    };
  }

  private handleAppStateChange(nextState: AppStateStatus): void {
    if (nextState === 'active') {
      this.sync('app_foreground');
    }
  }

  private getSortedTasks(): SyncTask[] {
    const tasks = Array.from(this.tasks.values());

    // Sort by priority (higher first), then by last sync time (oldest first)
    return tasks.sort((a, b) => {
      // Priority items go first
      const aIsPriority = this.config.priorityItems.includes(a.key);
      const bIsPriority = this.config.priorityItems.includes(b.key);

      if (aIsPriority && !bIsPriority) return -1;
      if (!aIsPriority && bIsPriority) return 1;

      // Then by priority value
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }

      // Then by last sync time
      const aLastSync = a.lastSync ?? 0;
      const bLastSync = b.lastSync ?? 0;
      return aLastSync - bLastSync;
    });
  }

  private registerDefaultTasks(): void {
    // Feed sync task
    this.registerTask({
      key: 'feed',
      name: 'Feed',
      priority: 100,
      lastSync: null,
      syncFn: async () => {
        const { api } = await import('./api');
        const data = await api.getFeed(1, 20);
        await offlineSupport.setCache('feed:for-you:1', data, 5 * 60 * 1000);
      },
    });

    // Inbox sync task
    this.registerTask({
      key: 'inbox',
      name: 'Inbox',
      priority: 90,
      lastSync: null,
      syncFn: async () => {
        const { api } = await import('./api');
        const data = await api.getInbox();
        await offlineSupport.setCache('inbox:messages', data, 5 * 60 * 1000);
      },
    });

    // Trends sync task
    this.registerTask({
      key: 'trends',
      name: 'Trends',
      priority: 50,
      lastSync: null,
      syncFn: async () => {
        const { api } = await import('./api');
        const data = await api.getTrends();
        await offlineSupport.setCache('trends:all', data, 15 * 60 * 1000);
      },
    });

    // Analytics sync task (lower priority, less frequent)
    this.registerTask({
      key: 'analytics',
      name: 'Analytics',
      priority: 30,
      lastSync: null,
      syncFn: async () => {
        const { api } = await import('./api');
        const data = await api.getAnalyticsOverview();
        await offlineSupport.setCache('analytics:overview', data, 30 * 60 * 1000);
      },
      shouldSync: (state) => {
        // Only sync analytics on WiFi
        return state.connectionType === 'wifi';
      },
    });
  }
}

// Create singleton
const syncManager = new SyncManager();

/**
 * Initialize background sync
 */
export async function initializeSync(config?: Partial<SyncConfig>): Promise<void> {
  if (config) {
    Object.assign(syncManager, new SyncManager(config));
  }
  await syncManager.initialize();
}

/**
 * Trigger a sync
 */
export function sync(trigger?: string): Promise<SyncResult> {
  return syncManager.sync(trigger);
}

/**
 * Sync a specific task
 */
export function syncTask(key: string): Promise<boolean> {
  return syncManager.syncTask(key);
}

/**
 * Get sync status
 */
export function getSyncStatus() {
  return syncManager.getStatus();
}

/**
 * Register a custom sync task
 */
export function registerSyncTask(task: SyncTask): void {
  syncManager.registerTask(task);
}

/**
 * Stop sync manager
 */
export function stopSync(): void {
  syncManager.destroy();
}

export { SyncManager };
export default syncManager;
