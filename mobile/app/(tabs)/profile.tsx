/**
 * Profile Screen
 *
 * User profile with content grid, stats, and settings.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  Image,
  FlatList,
  StyleSheet,
  Pressable,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { PostGridItem } from '@/components/profile/PostGridItem';
import { ProfileStats } from '@/components/profile/ProfileStats';
import { useTheme } from '@/lib/theme';
import { useAuth } from '@/lib/auth';
import { useProfile } from '@/hooks/useProfile';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GRID_SPACING = 2;
const NUM_COLUMNS = 3;
const ITEM_SIZE = (SCREEN_WIDTH - GRID_SPACING * (NUM_COLUMNS - 1)) / NUM_COLUMNS;

type TabType = 'posts' | 'analytics' | 'saved';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const { user } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('posts');

  const { profile, posts, isLoading } = useProfile(user?.id);

  const renderPost = useCallback(
    ({ item, index }: { item: any; index: number }) => (
      <PostGridItem
        post={item}
        size={ITEM_SIZE}
        onPress={() => router.push(`/post/${item.id}`)}
      />
    ),
    [router]
  );

  const ListHeader = useCallback(
    () => (
      <View style={styles.headerContainer}>
        {/* Profile Info */}
        <View style={styles.profileSection}>
          <Image
            source={{ uri: profile?.avatar_url || 'https://via.placeholder.com/100' }}
            style={styles.avatar}
          />

          <View style={styles.profileInfo}>
            <Text style={[styles.displayName, { color: colors.text }]}>
              {profile?.display_name || 'User'}
            </Text>
            <Text style={[styles.username, { color: colors.textSecondary }]}>
              @{profile?.username || 'username'}
            </Text>
            {profile?.bio && (
              <Text style={[styles.bio, { color: colors.text }]} numberOfLines={3}>
                {profile.bio}
              </Text>
            )}
          </View>
        </View>

        {/* Stats */}
        <ProfileStats
          posts={profile?.post_count || 0}
          followers={profile?.follower_count || 0}
          following={profile?.following_count || 0}
        />

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <Pressable
            style={[styles.editButton, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/settings/profile')}
          >
            <Text style={[styles.editButtonText, { color: colors.text }]}>
              Edit Profile
            </Text>
          </Pressable>

          <Pressable
            style={[styles.iconButton, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/settings')}
          >
            <Ionicons name="settings-outline" size={20} color={colors.text} />
          </Pressable>
        </View>

        {/* Tab Bar */}
        <View style={[styles.tabBar, { borderBottomColor: colors.border }]}>
          <Pressable
            style={styles.tabItem}
            onPress={() => setActiveTab('posts')}
          >
            <Ionicons
              name="grid-outline"
              size={24}
              color={activeTab === 'posts' ? colors.primary : colors.textSecondary}
            />
          </Pressable>

          <Pressable
            style={styles.tabItem}
            onPress={() => setActiveTab('analytics')}
          >
            <Ionicons
              name="stats-chart-outline"
              size={24}
              color={activeTab === 'analytics' ? colors.primary : colors.textSecondary}
            />
          </Pressable>

          <Pressable
            style={styles.tabItem}
            onPress={() => setActiveTab('saved')}
          >
            <Ionicons
              name="bookmark-outline"
              size={24}
              color={activeTab === 'saved' ? colors.primary : colors.textSecondary}
            />
          </Pressable>
        </View>
      </View>
    ),
    [profile, colors, activeTab, router]
  );

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.background, paddingTop: insets.top },
      ]}
    >
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        numColumns={NUM_COLUMNS}
        ListHeaderComponent={ListHeader}
        columnWrapperStyle={styles.gridRow}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="images-outline" size={48} color={colors.textSecondary} />
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              No posts yet
            </Text>
            <Pressable
              style={[styles.createButton, { backgroundColor: colors.primary }]}
              onPress={() => router.push('/create')}
            >
              <Text style={styles.createButtonText}>Create Your First Post</Text>
            </Pressable>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerContainer: {
    paddingBottom: 4,
  },
  profileSection: {
    flexDirection: 'row',
    padding: 16,
    gap: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  profileInfo: {
    flex: 1,
    justifyContent: 'center',
    gap: 4,
  },
  displayName: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  username: {
    fontSize: 14,
  },
  bio: {
    fontSize: 14,
    marginTop: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 8,
  },
  editButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 0.5,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
  },
  gridRow: {
    gap: GRID_SPACING,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
  createButton: {
    marginTop: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  createButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
});
