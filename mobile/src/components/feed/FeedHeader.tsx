/**
 * Feed Header Component
 *
 * Top navigation for feed with "For You" / "Following" tabs.
 */

import { useState } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';

import { useTheme } from '@/lib/theme';

interface FeedHeaderProps {
  activeTab?: 'for_you' | 'following';
  onTabChange?: (tab: 'for_you' | 'following') => void;
}

export function FeedHeader({
  activeTab = 'for_you',
  onTabChange,
}: FeedHeaderProps) {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();

  const handleTabPress = (tab: 'for_you' | 'following') => {
    Haptics.selectionAsync();
    onTabChange?.(tab);
  };

  return (
    <View
      style={[
        styles.container,
        { paddingTop: insets.top + 8 },
      ]}
    >
      {/* Live Button */}
      <Pressable
        style={styles.iconButton}
        onPress={() => router.push('/live')}
      >
        <Ionicons name="radio-outline" size={24} color="#FFF" />
      </Pressable>

      {/* Tabs */}
      <View style={styles.tabs}>
        <Pressable
          style={styles.tab}
          onPress={() => handleTabPress('following')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'following' && styles.tabTextActive,
            ]}
          >
            Following
          </Text>
          {activeTab === 'following' && <View style={styles.tabIndicator} />}
        </Pressable>

        <Pressable
          style={styles.tab}
          onPress={() => handleTabPress('for_you')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'for_you' && styles.tabTextActive,
            ]}
          >
            For You
          </Text>
          {activeTab === 'for_you' && <View style={styles.tabIndicator} />}
        </Pressable>
      </View>

      {/* Search Button */}
      <Pressable
        style={styles.iconButton}
        onPress={() => router.push('/discover')}
      >
        <Ionicons name="search-outline" size={24} color="#FFF" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 8,
    zIndex: 10,
  },
  iconButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabs: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  tab: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  tabText: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 17,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#FFF',
  },
  tabIndicator: {
    position: 'absolute',
    bottom: 0,
    width: 30,
    height: 2,
    backgroundColor: '#FFF',
    borderRadius: 1,
  },
});
