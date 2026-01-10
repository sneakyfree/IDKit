/**
 * Profile Hook
 *
 * Fetch and manage user profile data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface Profile {
  id: string;
  user_id: string;
  display_name: string;
  username: string;
  bio?: string;
  avatar_url?: string;
  cover_image_url?: string;
  website_url?: string;
  follower_count: number;
  following_count: number;
  post_count: number;
  is_verified: boolean;
  is_following?: boolean;
}

export function useProfile(userId?: string) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const targetId = userId || user?.id;
  const isOwnProfile = targetId === user?.id;

  const profileQuery = useQuery<Profile>({
    queryKey: ['profile', targetId],
    queryFn: async () => {
      // For own profile, we already have some data from auth
      if (isOwnProfile && user) {
        const profile = await api.get(`/profiles/${user.username}`);
        return profile as Profile;
      }
      // For other profiles, fetch by ID
      return api.get(`/profiles/by-id/${targetId}`) as Promise<Profile>;
    },
    enabled: !!targetId,
  });

  const postsQuery = useQuery({
    queryKey: ['profile', targetId, 'posts'],
    queryFn: async () => {
      if (!profileQuery.data?.username) return [];
      const result = await api.get(`/profiles/${profileQuery.data.username}/posts`);
      return result.posts || [];
    },
    enabled: !!profileQuery.data?.username,
  });

  const followMutation = useMutation({
    mutationFn: (username: string) => api.followUser(username),
    onMutate: async (username) => {
      await queryClient.cancelQueries({ queryKey: ['profile', targetId] });

      const previousProfile = queryClient.getQueryData(['profile', targetId]);

      queryClient.setQueryData(['profile', targetId], (old: any) => ({
        ...old,
        is_following: true,
        follower_count: (old?.follower_count || 0) + 1,
      }));

      return { previousProfile };
    },
    onError: (err, username, context) => {
      if (context?.previousProfile) {
        queryClient.setQueryData(['profile', targetId], context.previousProfile);
      }
    },
  });

  const unfollowMutation = useMutation({
    mutationFn: (username: string) => api.unfollowUser(username),
    onMutate: async (username) => {
      await queryClient.cancelQueries({ queryKey: ['profile', targetId] });

      const previousProfile = queryClient.getQueryData(['profile', targetId]);

      queryClient.setQueryData(['profile', targetId], (old: any) => ({
        ...old,
        is_following: false,
        follower_count: Math.max((old?.follower_count || 0) - 1, 0),
      }));

      return { previousProfile };
    },
    onError: (err, username, context) => {
      if (context?.previousProfile) {
        queryClient.setQueryData(['profile', targetId], context.previousProfile);
      }
    },
  });

  return {
    profile: profileQuery.data,
    posts: postsQuery.data || [],
    isLoading: profileQuery.isLoading,
    isOwnProfile,
    follow: followMutation.mutate,
    unfollow: unfollowMutation.mutate,
    isFollowing: profileQuery.data?.is_following || false,
  };
}
