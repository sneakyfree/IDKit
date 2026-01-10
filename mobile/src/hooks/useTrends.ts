/**
 * Trends Hook
 *
 * Fetch and manage trending content.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface Trend {
  id: string;
  name: string;
  category: string;
  platforms: string[];
  volume: number;
  velocity: string;
  growth_rate: number;
  engagement_rate: number;
  opportunity_score: float;
  related_hashtags: string[];
}

interface TrendsData {
  hashtags: Trend[];
  topics: Trend[];
  users: any[];
}

export function useTrends(platforms?: string[]) {
  return useQuery<TrendsData>({
    queryKey: ['trends', platforms],
    queryFn: async () => {
      const trends = await api.getTrends(platforms);
      return {
        hashtags: trends.filter((t: any) => t.category === 'hashtag'),
        topics: trends.filter((t: any) => t.category === 'topic'),
        users: [], // Fetched separately
      };
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useTrendAlerts() {
  return useQuery({
    queryKey: ['trend-alerts'],
    queryFn: () => api.getTrendAlerts(),
    staleTime: 1000 * 60 * 5,
  });
}
