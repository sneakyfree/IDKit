/**
 * Feed Hook
 *
 * Infinite scroll feed with React Query.
 */

import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Post } from '@/types/feed';

interface FeedPage {
  posts: Post[];
  has_more: boolean;
}

export function useFeed(feedType: 'for_you' | 'following' = 'for_you') {
  const queryClient = useQueryClient();

  const query = useInfiniteQuery<FeedPage>({
    queryKey: ['feed', feedType],
    queryFn: async ({ pageParam = 1 }) => {
      if (feedType === 'following') {
        return api.getFollowingFeed(pageParam as number);
      }
      return api.getFeed(pageParam as number);
    },
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.has_more) {
        return allPages.length + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
  });

  const likeMutation = useMutation({
    mutationFn: (postId: string) => api.likePost(postId),
    onMutate: async (postId) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['feed', feedType] });

      queryClient.setQueryData(['feed', feedType], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          pages: old.pages.map((page: FeedPage) => ({
            ...page,
            posts: page.posts.map((post: Post) =>
              post.id === postId
                ? { ...post, is_liked: true, like_count: post.like_count + 1 }
                : post
            ),
          })),
        };
      });
    },
  });

  const unlikeMutation = useMutation({
    mutationFn: (postId: string) => api.unlikePost(postId),
    onMutate: async (postId) => {
      await queryClient.cancelQueries({ queryKey: ['feed', feedType] });

      queryClient.setQueryData(['feed', feedType], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          pages: old.pages.map((page: FeedPage) => ({
            ...page,
            posts: page.posts.map((post: Post) =>
              post.id === postId
                ? { ...post, is_liked: false, like_count: post.like_count - 1 }
                : post
            ),
          })),
        };
      });
    },
  });

  const saveMutation = useMutation({
    mutationFn: (postId: string) => api.savePost(postId),
    onMutate: async (postId) => {
      await queryClient.cancelQueries({ queryKey: ['feed', feedType] });

      queryClient.setQueryData(['feed', feedType], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          pages: old.pages.map((page: FeedPage) => ({
            ...page,
            posts: page.posts.map((post: Post) =>
              post.id === postId
                ? { ...post, is_saved: !post.is_saved }
                : post
            ),
          })),
        };
      });
    },
  });

  return {
    ...query,
    isRefreshing: query.isRefetching && !query.isFetchingNextPage,
    likePost: likeMutation.mutate,
    unlikePost: unlikeMutation.mutate,
    savePost: saveMutation.mutate,
  };
}
