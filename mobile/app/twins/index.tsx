/**
 * AI Twin Lab Screen
 *
 * Create and manage AI twins with voice cloning and avatar training.
 * TikTok-simple design with progressive disclosure.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Pressable,
  Image,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '@/lib/theme';

type TabType = 'twins' | 'voices' | 'avatars';

// Mock AI Twin data
const mockTwins = [
  {
    id: '1',
    name: 'Professional Twin',
    description: 'Business and professional content voice',
    voiceCloned: true,
    avatarTrained: true,
    lastUsed: '2024-01-15',
    videosGenerated: 24,
  },
  {
    id: '2',
    name: 'Casual Twin',
    description: 'Casual, fun content for social media',
    voiceCloned: true,
    avatarTrained: false,
    lastUsed: '2024-01-10',
    videosGenerated: 12,
  },
];

const mockVoices = [
  { id: '1', name: 'Professional Voice', language: 'English (US)', gender: 'Female' },
  { id: '2', name: 'Casual Voice', language: 'English (US)', gender: 'Female' },
];

export default function TwinsScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('twins');

  const tabs: { key: TabType; label: string }[] = [
    { key: 'twins', label: 'Twins' },
    { key: 'voices', label: 'Voices' },
    { key: 'avatars', label: 'Avatars' },
  ];

  const renderTwinCard = useCallback(
    (twin: typeof mockTwins[0]) => (
      <Pressable
        key={twin.id}
        style={[styles.twinCard, { backgroundColor: colors.surface }]}
        onPress={() => router.push(`/twins/${twin.id}`)}
      >
        <LinearGradient
          colors={['#8B5CF6', '#EC4899', '#F97316']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.avatarGradient}
        >
          <View style={[styles.avatarInner, { backgroundColor: colors.surface }]}>
            <Ionicons name="person" size={32} color={colors.textSecondary} />
          </View>
        </LinearGradient>

        <View style={styles.twinInfo}>
          <Text style={[styles.twinName, { color: colors.text }]}>{twin.name}</Text>
          <Text style={[styles.twinDescription, { color: colors.textSecondary }]}>
            {twin.description}
          </Text>

          <View style={styles.statusRow}>
            <View style={styles.statusItem}>
              <Ionicons
                name={twin.voiceCloned ? 'checkmark-circle' : 'ellipse-outline'}
                size={16}
                color={twin.voiceCloned ? '#22C55E' : colors.textSecondary}
              />
              <Text style={[styles.statusText, { color: colors.textSecondary }]}>
                Voice
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Ionicons
                name={twin.avatarTrained ? 'checkmark-circle' : 'ellipse-outline'}
                size={16}
                color={twin.avatarTrained ? '#22C55E' : colors.textSecondary}
              />
              <Text style={[styles.statusText, { color: colors.textSecondary }]}>
                Avatar
              </Text>
            </View>
          </View>

          <Text style={[styles.twinStats, { color: colors.textTertiary }]}>
            {twin.videosGenerated} videos generated • Last used {twin.lastUsed}
          </Text>
        </View>

        <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
      </Pressable>
    ),
    [colors, router]
  );

  const renderVoiceCard = useCallback(
    (voice: typeof mockVoices[0]) => (
      <View
        key={voice.id}
        style={[styles.voiceCard, { backgroundColor: colors.surface }]}
      >
        <View style={[styles.voiceIcon, { backgroundColor: 'rgba(139, 92, 246, 0.2)' }]}>
          <Ionicons name="mic" size={20} color="#8B5CF6" />
        </View>
        <View style={styles.voiceInfo}>
          <Text style={[styles.voiceName, { color: colors.text }]}>{voice.name}</Text>
          <Text style={[styles.voiceDetails, { color: colors.textSecondary }]}>
            {voice.language} • {voice.gender}
          </Text>
        </View>
        <Pressable style={styles.playButton}>
          <Ionicons name="play" size={20} color={colors.text} />
        </Pressable>
      </View>
    ),
    [colors]
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'AI Twin Lab',
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerRight: () => (
            <Pressable
              onPress={() => router.push('/twins/create')}
              style={styles.headerButton}
            >
              <LinearGradient
                colors={['#8B5CF6', '#EC4899']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.headerButtonGradient}
              >
                <Text style={styles.headerButtonText}>+ New Twin</Text>
              </LinearGradient>
            </Pressable>
          ),
        }}
      />

      {/* Tabs */}
      <View style={[styles.tabContainer, { borderBottomColor: colors.border }]}>
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
          </Pressable>
        ))}
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: insets.bottom + 20 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {activeTab === 'twins' && (
          <>
            {/* Info Card */}
            <LinearGradient
              colors={['rgba(139, 92, 246, 0.3)', 'rgba(236, 72, 153, 0.3)']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.infoCard}
            >
              <View style={styles.infoIconContainer}>
                <Ionicons name="sparkles" size={24} color="#8B5CF6" />
              </View>
              <View style={styles.infoContent}>
                <Text style={[styles.infoTitle, { color: colors.text }]}>
                  Create Your AI Twin
                </Text>
                <Text style={[styles.infoDescription, { color: colors.textSecondary }]}>
                  Train your AI clone with your voice and appearance. Generate unlimited
                  videos, podcasts, and content automatically.
                </Text>
              </View>
            </LinearGradient>

            {/* Twin Cards */}
            {mockTwins.map(renderTwinCard)}

            {/* Create New Twin Card */}
            <Pressable
              style={[styles.createCard, { borderColor: colors.border }]}
              onPress={() => router.push('/twins/create')}
            >
              <View style={[styles.createIcon, { backgroundColor: colors.surface }]}>
                <Ionicons name="add" size={28} color={colors.textSecondary} />
              </View>
              <Text style={[styles.createTitle, { color: colors.text }]}>
                Create New AI Twin
              </Text>
              <Text style={[styles.createDescription, { color: colors.textSecondary }]}>
                Clone your voice and appearance
              </Text>
            </Pressable>
          </>
        )}

        {activeTab === 'voices' && (
          <>
            <View style={[styles.section, { backgroundColor: colors.surface }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Cloned Voices
              </Text>
              <View style={styles.voiceList}>
                {mockVoices.map(renderVoiceCard)}
              </View>
              <Pressable style={[styles.addButton, { backgroundColor: colors.surfaceHover }]}>
                <Text style={[styles.addButtonText, { color: colors.text }]}>
                  + Clone New Voice
                </Text>
              </Pressable>
            </View>

            <View style={[styles.section, { backgroundColor: colors.surface }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Voice Settings
              </Text>
              <View style={styles.settingRow}>
                <Text style={[styles.settingLabel, { color: colors.textSecondary }]}>
                  Default Voice
                </Text>
                <Pressable style={[styles.settingValue, { backgroundColor: colors.surfaceHover }]}>
                  <Text style={[styles.settingValueText, { color: colors.text }]}>
                    Professional Voice
                  </Text>
                  <Ionicons name="chevron-down" size={16} color={colors.textSecondary} />
                </Pressable>
              </View>
              <View style={styles.settingRow}>
                <Text style={[styles.settingLabel, { color: colors.textSecondary }]}>
                  Speaking Speed
                </Text>
                <View style={styles.speedIndicator}>
                  <Text style={[styles.speedValue, { color: colors.text }]}>1.0x</Text>
                </View>
              </View>
            </View>
          </>
        )}

        {activeTab === 'avatars' && (
          <>
            <View style={[styles.section, { backgroundColor: colors.surface }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Trained Avatars
              </Text>
              <View style={styles.avatarGrid}>
                <LinearGradient
                  colors={['#8B5CF6', '#EC4899', '#F97316']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.avatarGridItem}
                >
                  <View style={[styles.avatarGridInner, { backgroundColor: colors.surface }]}>
                    <Ionicons name="person" size={40} color={colors.textSecondary} />
                    <Text style={[styles.avatarLabel, { color: colors.textSecondary }]}>
                      Professional
                    </Text>
                  </View>
                </LinearGradient>

                <Pressable
                  style={[styles.avatarGridAdd, { borderColor: colors.border }]}
                  onPress={() => router.push('/twins/avatar/new')}
                >
                  <Ionicons name="add" size={32} color={colors.textSecondary} />
                  <Text style={[styles.avatarLabel, { color: colors.textSecondary }]}>
                    Train New
                  </Text>
                </Pressable>
              </View>
            </View>

            <View style={[styles.section, { backgroundColor: colors.surface }]}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Training Tips
              </Text>
              <View style={styles.tipsList}>
                {[
                  'Upload 10-20 high-quality photos',
                  'Use different angles and expressions',
                  'Good lighting improves results',
                  'Avoid sunglasses or heavy filters',
                ].map((tip, index) => (
                  <View key={index} style={styles.tipItem}>
                    <Ionicons name="checkmark" size={16} color="#22C55E" />
                    <Text style={[styles.tipText, { color: colors.textSecondary }]}>
                      {tip}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          </>
        )}
      </ScrollView>
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
  tabContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#8B5CF6',
  },
  tabText: {
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
  infoCard: {
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(139, 92, 246, 0.3)',
  },
  infoIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(139, 92, 246, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  infoDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  twinCard: {
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarGradient: {
    width: 64,
    height: 64,
    borderRadius: 12,
    padding: 2,
  },
  avatarInner: {
    flex: 1,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  twinInfo: {
    flex: 1,
  },
  twinName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  twinDescription: {
    fontSize: 14,
    marginBottom: 8,
  },
  statusRow: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 8,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 12,
  },
  twinStats: {
    fontSize: 12,
  },
  createCard: {
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
  },
  createIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  createTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  createDescription: {
    fontSize: 14,
  },
  section: {
    borderRadius: 16,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  voiceList: {
    gap: 12,
    marginBottom: 12,
  },
  voiceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  voiceIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceInfo: {
    flex: 1,
  },
  voiceName: {
    fontSize: 14,
    fontWeight: '500',
  },
  voiceDetails: {
    fontSize: 12,
  },
  playButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButton: {
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  addButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  settingRow: {
    marginBottom: 16,
  },
  settingLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  settingValue: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
  },
  settingValueText: {
    fontSize: 14,
  },
  speedIndicator: {
    alignItems: 'center',
  },
  speedValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  avatarGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  avatarGridItem: {
    flex: 1,
    aspectRatio: 1,
    borderRadius: 12,
    padding: 2,
  },
  avatarGridInner: {
    flex: 1,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  avatarGridAdd: {
    flex: 1,
    aspectRatio: 1,
    borderRadius: 12,
    borderWidth: 2,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  avatarLabel: {
    fontSize: 12,
  },
  tipsList: {
    gap: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tipText: {
    fontSize: 14,
  },
});
