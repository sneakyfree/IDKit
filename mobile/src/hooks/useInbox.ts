/**
 * Inbox Hook
 *
 * Manage notifications and messages.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useInbox() {
  const queryClient = useQueryClient();

  const notificationsQuery = useQuery({
    queryKey: ['inbox', 'notifications'],
    queryFn: () => api.getInbox({ message_type: 'comment' }),
  });

  const messagesQuery = useQuery({
    queryKey: ['inbox', 'messages'],
    queryFn: () => api.getConversations(),
  });

  const statsQuery = useQuery({
    queryKey: ['inbox', 'stats'],
    queryFn: () => api.getInboxStats(),
    staleTime: 1000 * 60, // 1 minute
  });

  const markAsReadMutation = useMutation({
    mutationFn: (messageId: string) =>
      api.post(`/inbox/messages/${messageId}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });

  const refetch = () => {
    notificationsQuery.refetch();
    messagesQuery.refetch();
    statsQuery.refetch();
  };

  return {
    notifications: notificationsQuery.data?.messages || [],
    messages: messagesQuery.data?.conversations || [],
    isLoading: notificationsQuery.isLoading || messagesQuery.isLoading,
    isRefreshing:
      notificationsQuery.isRefetching || messagesQuery.isRefetching,
    refetch,
    markAsRead: markAsReadMutation.mutate,
    unreadCount: {
      activity: statsQuery.data?.unread_comments || 0,
      messages: statsQuery.data?.unread_dms || 0,
    },
  };
}
