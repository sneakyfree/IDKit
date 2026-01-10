/**
 * Discover Screen
 *
 * Search and explore content, users, and trends.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  StyleSheet,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { TrendingHashtags } from '@/components/discover/TrendingHashtags';
import { TrendingUsers } from '@/components/discover/TrendingUsers';
import { SearchResults } from '@/components/discover/SearchResults';
import { useTheme } from '@/lib/theme';
import { useTrends } from '@/hooks/useTrends';
import { useSearch } from '@/hooks/useSearch';

type TabType = 'trending' | 'users' | 'hashtags';

export default function DiscoverScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('trending');

  const { data: trends, isLoading: trendsLoading } = useTrends();
  const { data: searchResults, isLoading: searchLoading } = useSearch(searchQuery);

  const handleSearch = useCallback((text: string) => {
    setSearchQuery(text);
    setIsSearching(text.length > 0);
  }, []);

  const tabs: { key: TabType; label: string }[] = [
    { key: 'trending', label: 'Trending' },
    { key: 'users', label: 'Users' },
    { key: 'hashtags', label: 'Hashtags' },
  ];

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: colors.background, paddingTop: insets.top },
      ]}
    >
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View
          style={[styles.searchBar, { backgroundColor: colors.surface }]}
        >
          <Ionicons name="search" size={20} color={colors.textSecondary} />
          <TextInput
            style={[styles.searchInput, { color: colors.text }]}
            placeholder="Search users, hashtags, content..."
            placeholderTextColor={colors.textSecondary}
            value={searchQuery}
            onChangeText={handleSearch}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {searchQuery.length > 0 && (
            <Pressable onPress={() => handleSearch('')}>
              <Ionicons name="close-circle" size={20} color={colors.textSecondary} />
            </Pressable>
          )}
        </View>
      </View>

      {/* Show search results or discovery content */}
      {isSearching ? (
        <SearchResults
          query={searchQuery}
          results={searchResults}
          isLoading={searchLoading}
        />
      ) : (
        <>
          {/* Tabs */}
          <View style={styles.tabContainer}>
            {tabs.map((tab) => (
              <Pressable
                key={tab.key}
                style={[
                  styles.tab,
                  activeTab === tab.key && {
                    borderBottomColor: colors.primary,
                    borderBottomWidth: 2,
                  },
                ]}
                onPress={() => setActiveTab(tab.key)}
              >
                <Text
                  style={[
                    styles.tabText,
                    {
                      color:
                        activeTab === tab.key
                          ? colors.primary
                          : colors.textSecondary,
                    },
                  ]}
                >
                  {tab.label}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Tab Content */}
          <View style={styles.content}>
            {activeTab === 'trending' && (
              <TrendingHashtags trends={trends?.hashtags ?? []} />
            )}
            {activeTab === 'users' && (
              <TrendingUsers users={trends?.users ?? []} />
            )}
            {activeTab === 'hashtags' && (
              <TrendingHashtags
                trends={trends?.hashtags ?? []}
                showAll
              />
            )}
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  searchContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    padding: 0,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    borderBottomWidth: 0.5,
    borderBottomColor: '#333',
  },
  tab: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginRight: 8,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
});
