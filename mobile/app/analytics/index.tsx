/**
 * Analytics Screen
 *
 * Comprehensive analytics dashboard for content performance.
 * TikTok-simple design with actionable insights.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Pressable,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '@/lib/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type TimeRange = '7d' | '30d' | '90d' | 'all';

// Mock analytics data
const mockOverview = {
  totalFollowers: 12500,
  followerChange: 342,
  followerChangePercent: 2.8,
  totalViews: 245000,
  viewChange: 18500,
  viewChangePercent: 8.2,
  totalEngagements: 15600,
  engagementRate: 6.4,
  engagementChange: 0.3,
};

const mockPlatformStats = [
  { platform: 'TikTok', followers: 5200, views: 125000, growth: 5.2, color: '#EC4899' },
  { platform: 'Instagram', followers: 4100, views: 68000, growth: 2.1, color: '#8B5CF6' },
  { platform: 'YouTube', followers: 2800, views: 42000, growth: 3.8, color: '#EF4444' },
  { platform: 'Twitter/X', followers: 400, views: 10000, growth: 1.5, color: '#3B82F6' },
];

const mockTopContent = [
  { id: '1', title: 'How AI is Changing Everything', platform: 'TikTok', views: 45200, engagement: 8.2 },
  { id: '2', title: 'Morning Routine 2024', platform: 'Instagram', views: 28900, engagement: 6.8 },
  { id: '3', title: 'Tech Review: Latest Gadgets', platform: 'YouTube', views: 18400, engagement: 5.5 },
];

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

export default function AnalyticsScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');

  const timeRanges: { key: TimeRange; label: string }[] = [
    { key: '7d', label: '7 Days' },
    { key: '30d', label: '30 Days' },
    { key: '90d', label: '90 Days' },
    { key: 'all', label: 'All Time' },
  ];

  const renderStatCard = useCallback(
    (
      icon: keyof typeof Ionicons.glyphMap,
      label: string,
      value: string,
      change?: { value: string; positive: boolean }
    ) => (
      <View style={[styles.statCard, { backgroundColor: colors.surface }]}>
        <View style={styles.statHeader}>
          <Ionicons name={icon} size={16} color={colors.textSecondary} />
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
            {label}
          </Text>
        </View>
        <Text style={[styles.statValue, { color: colors.text }]}>{value}</Text>
        {change && (
          <View style={styles.statChange}>
            <Ionicons
              name={change.positive ? 'trending-up' : 'trending-down'}
              size={16}
              color={change.positive ? '#22C55E' : '#EF4444'}
            />
            <Text
              style={[
                styles.statChangeText,
                { color: change.positive ? '#22C55E' : '#EF4444' },
              ]}
            >
              {change.value}
            </Text>
          </View>
        )}
      </View>
    ),
    [colors]
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Analytics',
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerRight: () => (
            <Pressable
              onPress={() => router.push('/analytics/export')}
              style={[styles.exportButton, { backgroundColor: colors.surface }]}
            >
              <Text style={[styles.exportButtonText, { color: colors.text }]}>
                Export
              </Text>
            </Pressable>
          ),
        }}
      />

      {/* Time Range Selector */}
      <View style={styles.timeRangeContainer}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.timeRangeScroll}
        >
          {timeRanges.map((range) => (
            <Pressable
              key={range.key}
              style={[
                styles.timeRangeButton,
                timeRange === range.key
                  ? styles.timeRangeActive
                  : { backgroundColor: colors.surface },
              ]}
              onPress={() => setTimeRange(range.key)}
            >
              <Text
                style={[
                  styles.timeRangeText,
                  {
                    color: timeRange === range.key ? '#000000' : colors.textSecondary,
                  },
                ]}
              >
                {range.label}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: insets.bottom + 20 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Overview Stats */}
        <View style={styles.statsGrid}>
          {renderStatCard(
            'people',
            'Followers',
            formatNumber(mockOverview.totalFollowers),
            {
              value: `+${formatNumber(mockOverview.followerChange)} (${mockOverview.followerChangePercent}%)`,
              positive: true,
            }
          )}
          {renderStatCard('eye', 'Views', formatNumber(mockOverview.totalViews), {
            value: `+${formatNumber(mockOverview.viewChange)} (${mockOverview.viewChangePercent}%)`,
            positive: true,
          })}
          {renderStatCard(
            'heart',
            'Engagements',
            formatNumber(mockOverview.totalEngagements),
            undefined
          )}
          {renderStatCard(
            'stats-chart',
            'Eng. Rate',
            `${mockOverview.engagementRate}%`,
            { value: `+${mockOverview.engagementChange}%`, positive: true }
          )}
        </View>

        {/* Platform Performance */}
        <View style={[styles.section, { backgroundColor: colors.surface }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            Platform Performance
          </Text>
          <View style={styles.platformList}>
            {mockPlatformStats.map((platform) => (
              <View key={platform.platform} style={styles.platformItem}>
                <View style={styles.platformHeader}>
                  <View style={styles.platformInfo}>
                    <View
                      style={[
                        styles.platformDot,
                        { backgroundColor: platform.color },
                      ]}
                    />
                    <Text style={[styles.platformName, { color: colors.text }]}>
                      {platform.platform}
                    </Text>
                  </View>
                  <Text style={[styles.platformFollowers, { color: colors.textSecondary }]}>
                    {formatNumber(platform.followers)} followers
                  </Text>
                </View>
                <View style={styles.progressContainer}>
                  <View
                    style={[styles.progressBar, { backgroundColor: colors.surfaceHover }]}
                  >
                    <View
                      style={[
                        styles.progressFill,
                        {
                          backgroundColor: platform.color,
                          width: `${(platform.views / mockOverview.totalViews) * 100}%`,
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.platformViews, { color: colors.textTertiary }]}>
                    {formatNumber(platform.views)} views
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Top Performing Content */}
        <View style={[styles.section, { backgroundColor: colors.surface }]}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Top Performing Content
            </Text>
            <Pressable onPress={() => router.push('/analytics/content')}>
              <Text style={styles.viewAllText}>View All</Text>
            </Pressable>
          </View>
          <View style={styles.contentList}>
            {mockTopContent.map((content, index) => (
              <View
                key={content.id}
                style={[styles.contentItem, { backgroundColor: colors.surfaceHover }]}
              >
                <View style={[styles.contentRank, { backgroundColor: colors.surface }]}>
                  <Text style={[styles.contentRankText, { color: colors.text }]}>
                    {index + 1}
                  </Text>
                </View>
                <View style={styles.contentInfo}>
                  <Text
                    style={[styles.contentTitle, { color: colors.text }]}
                    numberOfLines={1}
                  >
                    {content.title}
                  </Text>
                  <Text style={[styles.contentPlatform, { color: colors.textTertiary }]}>
                    {content.platform}
                  </Text>
                </View>
                <View style={styles.contentStats}>
                  <Text style={[styles.contentViews, { color: colors.text }]}>
                    {formatNumber(content.views)}
                  </Text>
                  <Text style={[styles.contentEngagement, { color: colors.textTertiary }]}>
                    {content.engagement}% eng.
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Quick Links */}
        <View style={styles.quickLinks}>
          <Pressable
            style={[styles.quickLink, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/analytics/audience')}
          >
            <Ionicons name="people" size={24} color="#8B5CF6" />
            <Text style={[styles.quickLinkTitle, { color: colors.text }]}>
              Audience Insights
            </Text>
            <Text style={[styles.quickLinkDesc, { color: colors.textTertiary }]}>
              Demographics & behavior
            </Text>
          </Pressable>
          <Pressable
            style={[styles.quickLink, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/analytics/trends')}
          >
            <Ionicons name="trending-up" size={24} color="#EC4899" />
            <Text style={[styles.quickLinkTitle, { color: colors.text }]}>
              Trend Radar
            </Text>
            <Text style={[styles.quickLinkDesc, { color: colors.textTertiary }]}>
              AI topic monitoring
            </Text>
          </Pressable>
          <Pressable
            style={[styles.quickLink, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/analytics/competitors')}
          >
            <Ionicons name="people-circle" size={24} color="#3B82F6" />
            <Text style={[styles.quickLinkTitle, { color: colors.text }]}>
              Competitor Analysis
            </Text>
            <Text style={[styles.quickLinkDesc, { color: colors.textTertiary }]}>
              Benchmark performance
            </Text>
          </Pressable>
          <Pressable
            style={[styles.quickLink, { backgroundColor: colors.surface }]}
            onPress={() => router.push('/analytics/viral')}
          >
            <Ionicons name="flash" size={24} color="#F97316" />
            <Text style={[styles.quickLinkTitle, { color: colors.text }]}>
              Viral Predictor
            </Text>
            <Text style={[styles.quickLinkDesc, { color: colors.textTertiary }]}>
              Score your content
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  exportButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  exportButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  timeRangeContainer: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  timeRangeScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  timeRangeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  timeRangeActive: {
    backgroundColor: '#FFFFFF',
  },
  timeRangeText: {
    fontSize: 14,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    gap: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statCard: {
    width: (SCREEN_WIDTH - 44) / 2,
    borderRadius: 16,
    padding: 16,
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 14,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  statChange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statChangeText: {
    fontSize: 14,
  },
  section: {
    borderRadius: 16,
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  viewAllText: {
    fontSize: 14,
    color: '#8B5CF6',
  },
  platformList: {
    gap: 16,
  },
  platformItem: {
    gap: 8,
  },
  platformHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  platformInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  platformDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  platformName: {
    fontSize: 14,
    fontWeight: '500',
  },
  platformFollowers: {
    fontSize: 14,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressBar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  platformViews: {
    fontSize: 12,
    width: 80,
    textAlign: 'right',
  },
  contentList: {
    gap: 12,
  },
  contentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  contentRank: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contentRankText: {
    fontSize: 14,
    fontWeight: '700',
  },
  contentInfo: {
    flex: 1,
  },
  contentTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  contentPlatform: {
    fontSize: 12,
  },
  contentStats: {
    alignItems: 'flex-end',
  },
  contentViews: {
    fontSize: 14,
    fontWeight: '500',
  },
  contentEngagement: {
    fontSize: 12,
  },
  quickLinks: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  quickLink: {
    width: (SCREEN_WIDTH - 44) / 2,
    borderRadius: 16,
    padding: 16,
  },
  quickLinkTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 8,
    marginBottom: 2,
  },
  quickLinkDesc: {
    fontSize: 12,
  },
});
