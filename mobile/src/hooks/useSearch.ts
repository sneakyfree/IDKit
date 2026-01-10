/**
 * Search Hook
 *
 * Search for users, posts, and hashtags.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useDebounce } from './useDebounce';

interface SearchResults {
  users: any[];
  posts: any[];
  hashtags: any[];
}

export function useSearch(query: string) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery<SearchResults>({
    queryKey: ['search', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) {
        return { users: [], posts: [], hashtags: [] };
      }

      const [users, posts] = await Promise.all([
        api.get('/search/users', { params: { q: debouncedQuery } }),
        api.get('/search/posts', { params: { q: debouncedQuery } }),
      ]);

      return {
        users: users.results || [],
        posts: posts.results || [],
        hashtags: [], // Extract from posts/users
      };
    },
    enabled: debouncedQuery.length >= 2,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}
