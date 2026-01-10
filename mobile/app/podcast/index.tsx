/**
 * Podcast Lab Screen
 *
 * "Insta Podcast" - One-click podcast episode generation.
 * TikTok-simple design with powerful AI capabilities.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Pressable,
  Modal,
  TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '@/lib/theme';

// Mock podcast data
const mockPodcast = {
  id: '1',
  title: 'Tech Talk with Jane',
  description: 'Weekly discussions about technology, AI, and the future',
  episodeCount: 24,
  subscriberCount: 5200,
  totalPlays: 45000,
};

const mockEpisodes = [
  {
    id: '1',
    title: 'AI Trends 2024 - What to Expect',
    description: 'A deep dive into the AI trends shaping 2024',
    duration: 1845,
    status: 'published',
    publishedAt: '2024-01-15',
    plays: 3200,
  },
  {
    id: '2',
    title: 'Building Your Personal Brand',
    description: 'How to build and maintain a strong personal brand online',
    duration: 2100,
    status: 'published',
    publishedAt: '2024-01-08',
    plays: 2800,
  },
  {
    id: '3',
    title: 'The Future of Content Creation',
    description: 'Exploring how AI is changing content creation',
    duration: 0,
    status: 'draft',
    publishedAt: null,
    plays: 0,
  },
];

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function PodcastScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [topic, setTopic] = useState('');
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
  const [selectedDuration, setSelectedDuration] = useState<string | null>(null);
  const [useAiTwin, setUseAiTwin] = useState(true);

  const styles_list = ['Conversational', 'Educational', 'Storytelling'];
  const durations = ['5 min', '10 min', '15 min', '30 min'];

  const renderEpisodeCard = useCallback(
    (episode: typeof mockEpisodes[0]) => (
      <Pressable
        key={episode.id}
        style={[styles.episodeCard, { backgroundColor: colors.surface }]}
        onPress={() => router.push(`/podcast/episodes/${episode.id}`)}
      >
        <View style={[styles.episodeThumb, { backgroundColor: colors.surfaceHover }]}>
          <Ionicons name="mic" size={24} color={colors.textSecondary} />
        </View>

        <View style={styles.episodeInfo}>
          <View style={styles.episodeHeader}>
            <Text
              style={[styles.episodeTitle, { color: colors.text }]}
              numberOfLines={1}
            >
              {episode.title}
            </Text>
            {episode.status === 'draft' && (
              <View style={[styles.draftBadge, { backgroundColor: colors.surfaceHover }]}>
                <Text style={[styles.draftText, { color: colors.textSecondary }]}>
                  Draft
                </Text>
              </View>
            )}
          </View>
          <Text
            style={[styles.episodeDescription, { color: colors.textSecondary }]}
            numberOfLines={2}
          >
            {episode.description}
          </Text>
          <View style={styles.episodeMeta}>
            {episode.duration > 0 && (
              <Text style={[styles.metaText, { color: colors.textTertiary }]}>
                {formatDuration(episode.duration)}
              </Text>
            )}
            {episode.publishedAt && (
              <Text style={[styles.metaText, { color: colors.textTertiary }]}>
                {episode.publishedAt}
              </Text>
            )}
            {episode.plays > 0 && (
              <Text style={[styles.metaText, { color: colors.textTertiary }]}>
                {formatNumber(episode.plays)} plays
              </Text>
            )}
          </View>
        </View>

        {episode.status === 'published' && (
          <Pressable
            style={styles.playButton}
            onPress={(e) => {
              e.stopPropagation();
              // Play episode
            }}
          >
            <LinearGradient
              colors={['#8B5CF6', '#EC4899']}
              style={styles.playButtonGradient}
            >
              <Ionicons name="play" size={20} color="#FFFFFF" style={{ marginLeft: 2 }} />
            </LinearGradient>
          </Pressable>
        )}
      </Pressable>
    ),
    [colors, router]
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Podcast Lab',
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerRight: () => (
            <Pressable
              onPress={() => setShowCreateModal(true)}
              style={styles.headerButton}
            >
              <LinearGradient
                colors={['#8B5CF6', '#EC4899']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.headerButtonGradient}
              >
                <Text style={styles.headerButtonText}>+ New Episode</Text>
              </LinearGradient>
            </Pressable>
          ),
        }}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: insets.bottom + 20 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Insta Podcast Banner */}
        <LinearGradient
          colors={['rgba(139, 92, 246, 0.3)', 'rgba(236, 72, 153, 0.3)']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.instaBanner}
        >
          <View style={styles.instaIconContainer}>
            <Ionicons name="sparkles" size={24} color="#8B5CF6" />
          </View>
          <View style={styles.instaContent}>
            <Text style={[styles.instaTitle, { color: colors.text }]}>
              Insta Podcast
            </Text>
            <Text style={[styles.instaDescription, { color: colors.textSecondary }]}>
              Generate a complete episode from just a topic. AI writes the script,
              clones your voice, and creates the video.
            </Text>
            <Pressable
              style={styles.instaButton}
              onPress={() => setShowCreateModal(true)}
            >
              <LinearGradient
                colors={['#8B5CF6', '#7C3AED']}
                style={styles.instaButtonGradient}
              >
                <Text style={styles.instaButtonText}>Generate Episode</Text>
              </LinearGradient>
            </Pressable>
          </View>
        </LinearGradient>

        {/* Podcast Info Card */}
        <View style={[styles.podcastCard, { backgroundColor: colors.surface }]}>
          <View style={styles.podcastHeader}>
            <LinearGradient
              colors={['#8B5CF6', '#EC4899']}
              style={styles.podcastCover}
            >
              <Ionicons name="mic" size={40} color="#FFFFFF" />
            </LinearGradient>

            <View style={styles.podcastInfo}>
              <Text style={[styles.podcastTitle, { color: colors.text }]}>
                {mockPodcast.title}
              </Text>
              <Text
                style={[styles.podcastDescription, { color: colors.textSecondary }]}
                numberOfLines={2}
              >
                {mockPodcast.description}
              </Text>
              <Text style={[styles.podcastMeta, { color: colors.textTertiary }]}>
                {mockPodcast.episodeCount} episodes • {formatNumber(mockPodcast.subscriberCount)} subscribers
              </Text>
            </View>
          </View>

          {/* Quick Stats */}
          <View style={styles.statsRow}>
            <View style={[styles.statItem, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.statValue, { color: colors.text }]}>
                {formatNumber(mockPodcast.totalPlays)}
              </Text>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
                Total Plays
              </Text>
            </View>
            <View style={[styles.statItem, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.statValue, { color: colors.text }]}>
                {mockPodcast.episodeCount}
              </Text>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
                Episodes
              </Text>
            </View>
            <View style={[styles.statItem, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.statValue, { color: colors.text }]}>
                {formatNumber(mockPodcast.subscriberCount)}
              </Text>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
                Subscribers
              </Text>
            </View>
          </View>

          {/* Actions */}
          <View style={styles.actionsRow}>
            <Pressable style={[styles.actionButton, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.actionText, { color: colors.text }]}>Settings</Text>
            </Pressable>
            <Pressable style={[styles.actionButton, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.actionText, { color: colors.text }]}>Analytics</Text>
            </Pressable>
            <Pressable style={[styles.actionButton, { backgroundColor: colors.surfaceHover }]}>
              <Text style={[styles.actionText, { color: colors.text }]}>Distribute</Text>
            </Pressable>
          </View>
        </View>

        {/* Episodes Section */}
        <View style={styles.episodesSection}>
          <View style={styles.episodesHeader}>
            <Text style={[styles.episodesTitle, { color: colors.text }]}>
              Episodes
            </Text>
            <Text style={[styles.episodesCount, { color: colors.textSecondary }]}>
              {mockEpisodes.length} total
            </Text>
          </View>

          {mockEpisodes.map(renderEpisodeCard)}
        </View>
      </ScrollView>

      {/* Create Episode Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <Pressable
            style={styles.modalBackdrop}
            onPress={() => setShowCreateModal(false)}
          />
          <View style={[styles.modalContent, { backgroundColor: colors.surface }]}>
            <View style={[styles.modalHandle, { backgroundColor: colors.border }]} />

            <Text style={[styles.modalTitle, { color: colors.text }]}>
              Create New Episode
            </Text>

            <View style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                  Episode Topic
                </Text>
                <TextInput
                  style={[
                    styles.textInput,
                    { backgroundColor: colors.surfaceHover, color: colors.text },
                  ]}
                  placeholder="e.g., The Future of AI in Marketing"
                  placeholderTextColor={colors.textTertiary}
                  value={topic}
                  onChangeText={setTopic}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                  Style
                </Text>
                <View style={styles.optionsRow}>
                  {styles_list.map((style) => (
                    <Pressable
                      key={style}
                      style={[
                        styles.optionButton,
                        { backgroundColor: colors.surfaceHover },
                        selectedStyle === style && styles.optionSelected,
                      ]}
                      onPress={() => setSelectedStyle(style)}
                    >
                      <Text
                        style={[
                          styles.optionText,
                          { color: selectedStyle === style ? '#FFFFFF' : colors.text },
                        ]}
                      >
                        {style}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                  Duration
                </Text>
                <View style={styles.optionsRow}>
                  {durations.map((duration) => (
                    <Pressable
                      key={duration}
                      style={[
                        styles.durationButton,
                        { backgroundColor: colors.surfaceHover },
                        selectedDuration === duration && styles.optionSelected,
                      ]}
                      onPress={() => setSelectedDuration(duration)}
                    >
                      <Text
                        style={[
                          styles.optionText,
                          { color: selectedDuration === duration ? '#FFFFFF' : colors.text },
                        ]}
                      >
                        {duration}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              <Pressable
                style={[styles.checkboxRow, { backgroundColor: colors.surfaceHover }]}
                onPress={() => setUseAiTwin(!useAiTwin)}
              >
                <Ionicons
                  name={useAiTwin ? 'checkbox' : 'square-outline'}
                  size={20}
                  color={useAiTwin ? '#8B5CF6' : colors.textSecondary}
                />
                <Text style={[styles.checkboxText, { color: colors.text }]}>
                  Use AI Twin voice and avatar
                </Text>
              </Pressable>

              <Pressable
                style={styles.generateButton}
                onPress={() => {
                  setShowCreateModal(false);
                  // Trigger generation
                }}
              >
                <LinearGradient
                  colors={['#8B5CF6', '#EC4899']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.generateButtonGradient}
                >
                  <Text style={styles.generateButtonText}>Generate Episode</Text>
                </LinearGradient>
              </Pressable>

              <Pressable
                onPress={() => {
                  setShowCreateModal(false);
                  router.push('/podcast/episodes/new');
                }}
              >
                <Text style={[styles.manualLink, { color: colors.textSecondary }]}>
                  Or create manually →
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerButton: {
    marginRight: 8,
  },
  headerButtonGradient: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  headerButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    gap: 16,
  },
  instaBanner: {
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(139, 92, 246, 0.3)',
  },
  instaIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(139, 92, 246, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  instaContent: {
    flex: 1,
  },
  instaTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  instaDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  instaButton: {
    alignSelf: 'flex-start',
  },
  instaButtonGradient: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  instaButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  podcastCard: {
    borderRadius: 16,
    padding: 16,
  },
  podcastHeader: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 16,
  },
  podcastCover: {
    width: 96,
    height: 96,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  podcastInfo: {
    flex: 1,
  },
  podcastTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  podcastDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  podcastMeta: {
    fontSize: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  statItem: {
    flex: 1,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 2,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  episodesSection: {
    gap: 12,
  },
  episodesHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  episodesTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  episodesCount: {
    fontSize: 14,
  },
  episodeCard: {
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  episodeThumb: {
    width: 64,
    height: 64,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  episodeInfo: {
    flex: 1,
  },
  episodeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  episodeTitle: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  draftBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  draftText: {
    fontSize: 12,
  },
  episodeDescription: {
    fontSize: 12,
    lineHeight: 16,
    marginBottom: 4,
  },
  episodeMeta: {
    flexDirection: 'row',
    gap: 12,
  },
  metaText: {
    fontSize: 12,
  },
  playButton: {
    marginLeft: 8,
  },
  playButtonGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
  },
  modalHandle: {
    width: 48,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 24,
  },
  modalBody: {
    gap: 20,
  },
  inputGroup: {
    gap: 8,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  textInput: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    fontSize: 14,
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  optionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  durationButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  optionSelected: {
    backgroundColor: '#8B5CF6',
  },
  optionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderRadius: 12,
  },
  checkboxText: {
    fontSize: 14,
  },
  generateButton: {
    marginTop: 8,
  },
  generateButtonGradient: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  generateButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  manualLink: {
    textAlign: 'center',
    fontSize: 14,
  },
});
