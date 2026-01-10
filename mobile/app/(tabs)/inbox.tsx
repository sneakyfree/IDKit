/**
 * Inbox Screen
 *
 * Notifications, comments, and DMs across all platforms.
 * Enhanced with AI Smart Reply suggestions.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Pressable,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

import { NotificationItem } from '@/components/inbox/NotificationItem';
import { MessageItem } from '@/components/inbox/MessageItem';
import { useTheme } from '@/lib/theme';
import { useInbox } from '@/hooks/useInbox';

type TabType = 'all' | 'comments' | 'mentions' | 'messages';

export default function InboxScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [showSmartReply, setShowSmartReply] = useState(true);

  const {
    notifications,
    messages,
    isLoading,
    isRefreshing,
    refetch,
    markAsRead,
    unreadCount,
  } = useInbox();

  const tabs: { key: TabType; label: string; count?: number }[] = [
    { key: 'all', label: 'All', count: unreadCount.activity + unreadCount.messages },
    { key: 'comments', label: 'Comments', count: unreadCount.comments },
    { key: 'mentions', label: 'Mentions', count: unreadCount.mentions },
    { key: 'messages', label: 'Messages', count: unreadCount.messages },
  ];

  const renderNotification = useCallback(
    ({ item }: { item: any }) => (
      <NotificationItem
        notification={item}
        onPress={() => markAsRead(item.id)}
      />
    ),
    [markAsRead]
  );

  const renderMessage = useCallback(
    ({ item }: { item: any }) => (
      <MessageItem
        conversation={item}
        onPress={() => {
          // Navigate to conversation
        }}
      />
    ),
    []
  );

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.background, paddingTop: insets.top },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Inbox</Text>
        <Pressable style={[styles.filterButton, { backgroundColor: colors.surface }]}>
          <Ionicons name="filter" size={20} color={colors.textSecondary} />
        </Pressable>
      </View>

      {/* Smart Reply Banner */}
      {showSmartReply && (
        <LinearGradient
          colors={['rgba(139, 92, 246, 0.2)', 'rgba(236, 72, 153, 0.2)']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.smartReplyBanner}
        >
          <View style={styles.smartReplyIcon}>
            <Ionicons name="sparkles" size={20} color="#8B5CF6" />
          </View>
          <View style={styles.smartReplyContent}>
            <Text style={[styles.smartReplyTitle, { color: colors.text }]}>
              Smart Reply Available
            </Text>
            <Text style={[styles.smartReplyDesc, { color: colors.textSecondary }]}>
              AI can help you respond to 12 unanswered comments
            </Text>
          </View>
          <Pressable
            style={styles.smartReplyButton}
            onPress={() => {
              // Navigate to smart reply
            }}
          >
            <Text style={styles.smartReplyButtonText}>Reply All</Text>
          </Pressable>
          <Pressable
            style={styles.dismissButton}
            onPress={() => setShowSmartReply(false)}
          >
            <Ionicons name="close" size={18} color={colors.textSecondary} />
          </Pressable>
        </LinearGradient>
      )}

      {/* Tab Bar */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={[styles.tabBar, { borderBottomColor: colors.border }]}
        contentContainerStyle={styles.tabBarContent}
      >
        {tabs.map((tab) => (
          <Pressable
            key={tab.key}
            style={[
              styles.tab,
              activeTab === tab.key && styles.activeTab,
            ]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text
              style={[
                styles.tabText,
                {
                  color: activeTab === tab.key ? colors.text : colors.textSecondary,
                },
              ]}
            >
              {tab.label}
            </Text>
            {tab.count && tab.count > 0 && (
              <View
                style={[
                  styles.badge,
                  {
                    backgroundColor:
                      activeTab === tab.key ? colors.primary : colors.surface,
                  },
                ]}
              >
                <Text
                  style={[
                    styles.badgeText,
                    { color: activeTab === tab.key ? '#FFF' : colors.textSecondary },
                  ]}
                >
                  {tab.count}
                </Text>
              </View>
            )}
          </Pressable>
        ))}
      </ScrollView>

      {/* Content */}
      {activeTab === 'messages' ? (
        <FlatList
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={refetch}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="chatbubbles-outline" size={48} color={colors.textSecondary} />
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                No messages yet
              </Text>
            </View>
          }
        />
      ) : (
        <FlatList
          data={notifications}
          renderItem={renderNotification}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={refetch}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons
                name={
                  activeTab === 'comments'
                    ? 'chatbox-outline'
                    : activeTab === 'mentions'
                    ? 'at-outline'
                    : 'notifications-outline'
                }
                size={48}
                color={colors.textSecondary}
              />
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                {activeTab === 'comments'
                  ? 'No comments yet'
                  : activeTab === 'mentions'
                  ? 'No mentions yet'
                  : 'No activity yet'}
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  filterButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  smartReplyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    gap: 10,
  },
  smartReplyIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(139, 92, 246, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  smartReplyContent: {
    flex: 1,
  },
  smartReplyTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  smartReplyDesc: {
    fontSize: 12,
    marginTop: 2,
  },
  smartReplyButton: {
    backgroundColor: '#8B5CF6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  smartReplyButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  dismissButton: {
    padding: 4,
  },
  tabBar: {
    borderBottomWidth: 0.5,
  },
  tabBarContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    gap: 6,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#8B5CF6',
  },
  tabText: {
    fontSize: 15,
    fontWeight: '600',
  },
  badge: {
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 5,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  listContent: {
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
});
