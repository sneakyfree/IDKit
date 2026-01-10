/**
 * Create Modal
 *
 * Universal content creation hub.
 * Quick Post | AI Video | Podcast | Schedule
 */

import { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';

import { useTheme } from '@/lib/theme';

type CreateOption = {
  id: string;
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
  route: string;
  color: string;
};

const CREATE_OPTIONS: CreateOption[] = [
  {
    id: 'quick-post',
    title: 'Quick Post',
    description: 'Text, image, or short video',
    icon: 'create-outline',
    route: '/create/quick-post',
    color: '#FF6B6B',
  },
  {
    id: 'ai-video',
    title: 'AI Video',
    description: 'Create with your AI Twin',
    icon: 'videocam-outline',
    route: '/create/ai-video',
    color: '#4ECDC4',
  },
  {
    id: 'podcast',
    title: 'Podcast Episode',
    description: 'One-click podcast creation',
    icon: 'mic-outline',
    route: '/create/podcast',
    color: '#9B59B6',
  },
  {
    id: 'schedule',
    title: 'Schedule Content',
    description: 'Plan your posts',
    icon: 'calendar-outline',
    route: '/create/schedule',
    color: '#3498DB',
  },
  {
    id: 'repurpose',
    title: 'Repurpose',
    description: 'Transform existing content',
    icon: 'repeat-outline',
    route: '/create/repurpose',
    color: '#F39C12',
  },
  {
    id: 'ai-script',
    title: 'AI Script',
    description: 'Generate content ideas',
    icon: 'bulb-outline',
    route: '/create/ai-script',
    color: '#1ABC9C',
  },
];

export default function CreateScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();

  const handleOptionPress = (option: CreateOption) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push(option.route as any);
  };

  const handleClose = () => {
    router.back();
  };

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.background, paddingTop: insets.top },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft} />
        <Text style={[styles.title, { color: colors.text }]}>Create</Text>
        <Pressable onPress={handleClose} style={styles.closeButton}>
          <Ionicons name="close" size={28} color={colors.text} />
        </Pressable>
      </View>

      {/* Create Options Grid */}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.grid}>
          {CREATE_OPTIONS.map((option) => (
            <Pressable
              key={option.id}
              style={({ pressed }) => [
                styles.optionCard,
                { backgroundColor: colors.surface },
                pressed && styles.optionCardPressed,
              ]}
              onPress={() => handleOptionPress(option)}
            >
              <View
                style={[
                  styles.iconContainer,
                  { backgroundColor: option.color + '20' },
                ]}
              >
                <Ionicons name={option.icon} size={28} color={option.color} />
              </View>
              <Text style={[styles.optionTitle, { color: colors.text }]}>
                {option.title}
              </Text>
              <Text
                style={[styles.optionDescription, { color: colors.textSecondary }]}
              >
                {option.description}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
            Quick Actions
          </Text>
          <View style={styles.quickActionsRow}>
            <Pressable
              style={[styles.quickAction, { backgroundColor: colors.surface }]}
              onPress={() => router.push('/camera')}
            >
              <Ionicons name="camera" size={24} color={colors.primary} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>
                Camera
              </Text>
            </Pressable>
            <Pressable
              style={[styles.quickAction, { backgroundColor: colors.surface }]}
              onPress={() => router.push('/create/upload')}
            >
              <Ionicons name="cloud-upload" size={24} color={colors.primary} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>
                Upload
              </Text>
            </Pressable>
            <Pressable
              style={[styles.quickAction, { backgroundColor: colors.surface }]}
              onPress={() => router.push('/create/drafts')}
            >
              <Ionicons name="document-text" size={24} color={colors.primary} />
              <Text style={[styles.quickActionText, { color: colors.text }]}>
                Drafts
              </Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
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
  headerLeft: {
    width: 40,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  closeButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  optionCard: {
    width: '48%',
    padding: 16,
    borderRadius: 16,
    gap: 8,
  },
  optionCardPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  iconContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  optionDescription: {
    fontSize: 12,
  },
  quickActions: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  quickActionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  quickAction: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    gap: 6,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '500',
  },
});
