/**
 * Trending Hashtags Component
 */

import { View, Text, FlatList, Pressable, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@/lib/theme';

interface TrendingHashtagsProps {
  trends: any[];
  showAll?: boolean;
}

export function TrendingHashtags({ trends, showAll = false }: TrendingHashtagsProps) {
  const { colors } = useTheme();
  const router = useRouter();

  const displayTrends = showAll ? trends : trends.slice(0, 10);

  const renderItem = ({ item, index }: { item: any; index: number }) => (
    <Pressable
      style={[styles.item, { backgroundColor: colors.surface }]}
      onPress={() => router.push(`/hashtag/${item.name.replace('#', '')}`)}
    >
      <View style={styles.rank}>
        <Text style={[styles.rankText, { color: colors.textSecondary }]}>
          {index + 1}
        </Text>
      </View>

      <View style={styles.content}>
        <Text style={[styles.hashtag, { color: colors.text }]}>
          {item.name.startsWith('#') ? item.name : `#${item.name}`}
        </Text>
        <Text style={[styles.stats, { color: colors.textSecondary }]}>
          {formatVolume(item.volume)} posts
        </Text>
      </View>

      <View style={[styles.velocityBadge, getVelocityStyle(item.velocity)]}>
        <Ionicons
          name={getVelocityIcon(item.velocity)}
          size={14}
          color="#FFF"
        />
        <Text style={styles.velocityText}>{item.velocity}</Text>
      </View>
    </Pressable>
  );

  return (
    <FlatList
      data={displayTrends}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
    />
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1000000) return (volume / 1000000).toFixed(1) + 'M';
  if (volume >= 1000) return (volume / 1000).toFixed(1) + 'K';
  return volume.toString();
}

function getVelocityIcon(velocity: string): keyof typeof Ionicons.glyphMap {
  switch (velocity) {
    case 'emerging':
      return 'flash';
    case 'rising':
      return 'trending-up';
    case 'peak':
      return 'flame';
    case 'declining':
      return 'trending-down';
    default:
      return 'remove';
  }
}

function getVelocityStyle(velocity: string) {
  switch (velocity) {
    case 'emerging':
      return { backgroundColor: '#9B59B6' };
    case 'rising':
      return { backgroundColor: '#00B894' };
    case 'peak':
      return { backgroundColor: '#FF6B6B' };
    case 'declining':
      return { backgroundColor: '#636E72' };
    default:
      return { backgroundColor: '#2D3436' };
  }
}

const styles = StyleSheet.create({
  list: {
    padding: 16,
    gap: 8,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  rank: {
    width: 28,
    alignItems: 'center',
  },
  rankText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    gap: 2,
  },
  hashtag: {
    fontSize: 15,
    fontWeight: '600',
  },
  stats: {
    fontSize: 12,
  },
  velocityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  velocityText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});
