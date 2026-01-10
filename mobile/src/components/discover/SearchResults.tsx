/**
 * Search Results Component
 */

import { View, Text, FlatList, Image, Pressable, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@/lib/theme';

interface SearchResultsProps {
  query: string;
  results: any;
  isLoading: boolean;
}

export function SearchResults({ query, results, isLoading }: SearchResultsProps) {
  const { colors } = useTheme();
  const router = useRouter();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  const hasUsers = results?.users?.length > 0;
  const hasPosts = results?.posts?.length > 0;
  const hasResults = hasUsers || hasPosts;

  if (!hasResults) {
    return (
      <View style={styles.empty}>
        <Ionicons name="search-outline" size={48} color={colors.textSecondary} />
        <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
          No results for "{query}"
        </Text>
      </View>
    );
  }

  return (
    <FlatList
      data={[
        ...(hasUsers ? [{ type: 'header', title: 'Users' }] : []),
        ...(results?.users || []).map((u: any) => ({ type: 'user', data: u })),
        ...(hasPosts ? [{ type: 'header', title: 'Posts' }] : []),
        ...(results?.posts || []).map((p: any) => ({ type: 'post', data: p })),
      ]}
      renderItem={({ item }) => {
        if (item.type === 'header') {
          return (
            <Text style={[styles.sectionHeader, { color: colors.textSecondary }]}>
              {item.title}
            </Text>
          );
        }

        if (item.type === 'user') {
          return (
            <Pressable
              style={[styles.userItem, { backgroundColor: colors.surface }]}
              onPress={() => router.push(`/profile/${item.data.username}`)}
            >
              <Image
                source={{ uri: item.data.avatar_url || 'https://via.placeholder.com/44' }}
                style={styles.userAvatar}
              />
              <View style={styles.userInfo}>
                <Text style={[styles.userName, { color: colors.text }]}>
                  {item.data.display_name}
                </Text>
                <Text style={[styles.userUsername, { color: colors.textSecondary }]}>
                  @{item.data.username}
                </Text>
              </View>
            </Pressable>
          );
        }

        if (item.type === 'post') {
          return (
            <Pressable
              style={[styles.postItem, { backgroundColor: colors.surface }]}
              onPress={() => router.push(`/post/${item.data.id}`)}
            >
              {item.data.thumbnail_url && (
                <Image
                  source={{ uri: item.data.thumbnail_url }}
                  style={styles.postThumbnail}
                />
              )}
              <View style={styles.postInfo}>
                <Text style={[styles.postText, { color: colors.text }]} numberOfLines={2}>
                  {item.data.content_text || 'Video post'}
                </Text>
                <Text style={[styles.postStats, { color: colors.textSecondary }]}>
                  {item.data.like_count} likes • {item.data.comment_count} comments
                </Text>
              </View>
            </Pressable>
          );
        }

        return null;
      }}
      keyExtractor={(item, index) => `${item.type}-${index}`}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  empty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
  list: {
    padding: 16,
    gap: 8,
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 8,
    marginBottom: 4,
  },
  userItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  userAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
  },
  userInfo: {
    flex: 1,
    gap: 2,
  },
  userName: {
    fontSize: 15,
    fontWeight: '600',
  },
  userUsername: {
    fontSize: 13,
  },
  postItem: {
    flexDirection: 'row',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  postThumbnail: {
    width: 60,
    height: 80,
    borderRadius: 8,
  },
  postInfo: {
    flex: 1,
    gap: 4,
  },
  postText: {
    fontSize: 14,
    lineHeight: 20,
  },
  postStats: {
    fontSize: 12,
  },
});
