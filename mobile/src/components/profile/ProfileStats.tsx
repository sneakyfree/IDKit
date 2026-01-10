/**
 * Profile Stats Component
 */

import { View, Text, Pressable, StyleSheet } from 'react-native';

import { useTheme } from '@/lib/theme';

interface ProfileStatsProps {
  posts: number;
  followers: number;
  following: number;
  onFollowersPress?: () => void;
  onFollowingPress?: () => void;
}

export function ProfileStats({
  posts,
  followers,
  following,
  onFollowersPress,
  onFollowingPress,
}: ProfileStatsProps) {
  const { colors } = useTheme();

  return (
    <View style={styles.container}>
      <View style={styles.stat}>
        <Text style={[styles.value, { color: colors.text }]}>
          {formatCount(posts)}
        </Text>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Posts</Text>
      </View>

      <Pressable style={styles.stat} onPress={onFollowersPress}>
        <Text style={[styles.value, { color: colors.text }]}>
          {formatCount(followers)}
        </Text>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Followers</Text>
      </Pressable>

      <Pressable style={styles.stat} onPress={onFollowingPress}>
        <Text style={[styles.value, { color: colors.text }]}>
          {formatCount(following)}
        </Text>
        <Text style={[styles.label, { color: colors.textSecondary }]}>Following</Text>
      </Pressable>
    </View>
  );
}

function formatCount(count: number): string {
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
  return count.toString();
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 40,
  },
  stat: {
    alignItems: 'center',
    gap: 2,
  },
  value: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  label: {
    fontSize: 13,
  },
});
