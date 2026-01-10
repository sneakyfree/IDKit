/**
 * Settings Screen
 *
 * User preferences, account settings, and app configuration.
 * TikTok-simple design with grouped sections.
 */

import { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Pressable,
  Switch,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';

import { useTheme } from '@/lib/theme';
import { useAuth } from '@/lib/auth';

type SettingItem = {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  type: 'link' | 'toggle' | 'action';
  value?: boolean;
  onPress?: () => void;
  danger?: boolean;
};

type SettingSection = {
  title: string;
  items: SettingItem[];
};

export default function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const router = useRouter();
  const { signOut } = useAuth();

  // Toggle states
  const [pushNotifications, setPushNotifications] = useState(true);
  const [emailDigest, setEmailDigest] = useState(true);
  const [commentNotifications, setCommentNotifications] = useState(true);
  const [followerNotifications, setFollowerNotifications] = useState(true);
  const [dmNotifications, setDmNotifications] = useState(true);
  const [autoPost, setAutoPost] = useState(false);
  const [aiAssist, setAiAssist] = useState(true);

  const handleSignOut = useCallback(() => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: () => signOut(),
        },
      ],
      { cancelable: true }
    );
  }, [signOut]);

  const handleDeleteAccount = useCallback(() => {
    Alert.alert(
      'Delete Account',
      'This action cannot be undone. All your data will be permanently deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // Handle delete
          },
        },
      ],
      { cancelable: true }
    );
  }, []);

  const sections: SettingSection[] = [
    {
      title: 'Account',
      items: [
        {
          id: 'profile',
          icon: 'person-circle',
          title: 'Edit Profile',
          subtitle: 'Name, bio, avatar',
          type: 'link',
          onPress: () => router.push('/profile/edit'),
        },
        {
          id: 'accounts',
          icon: 'share-social',
          title: 'Connected Accounts',
          subtitle: '3 platforms connected',
          type: 'link',
          onPress: () => router.push('/settings/accounts'),
        },
        {
          id: 'security',
          icon: 'shield-checkmark',
          title: 'Security',
          subtitle: 'Password, 2FA',
          type: 'link',
          onPress: () => router.push('/settings/security'),
        },
      ],
    },
    {
      title: 'Notifications',
      items: [
        {
          id: 'push',
          icon: 'notifications',
          title: 'Push Notifications',
          type: 'toggle',
          value: pushNotifications,
          onPress: () => setPushNotifications(!pushNotifications),
        },
        {
          id: 'email',
          icon: 'mail',
          title: 'Email Digest',
          subtitle: 'Weekly summary',
          type: 'toggle',
          value: emailDigest,
          onPress: () => setEmailDigest(!emailDigest),
        },
        {
          id: 'comments',
          icon: 'chatbubble',
          title: 'Comments',
          type: 'toggle',
          value: commentNotifications,
          onPress: () => setCommentNotifications(!commentNotifications),
        },
        {
          id: 'followers',
          icon: 'person-add',
          title: 'New Followers',
          type: 'toggle',
          value: followerNotifications,
          onPress: () => setFollowerNotifications(!followerNotifications),
        },
        {
          id: 'dms',
          icon: 'mail-open',
          title: 'Direct Messages',
          type: 'toggle',
          value: dmNotifications,
          onPress: () => setDmNotifications(!dmNotifications),
        },
      ],
    },
    {
      title: 'Content',
      items: [
        {
          id: 'autopost',
          icon: 'calendar',
          title: 'Auto-Post to Feed',
          subtitle: 'Share generated content automatically',
          type: 'toggle',
          value: autoPost,
          onPress: () => setAutoPost(!autoPost),
        },
        {
          id: 'aiassist',
          icon: 'sparkles',
          title: 'AI Assistant',
          subtitle: 'Smart suggestions enabled',
          type: 'toggle',
          value: aiAssist,
          onPress: () => setAiAssist(!aiAssist),
        },
        {
          id: 'brandvoice',
          icon: 'mic',
          title: 'Brand Voice',
          subtitle: 'Configure AI writing style',
          type: 'link',
          onPress: () => router.push('/settings/brand-voice'),
        },
        {
          id: 'templates',
          icon: 'document-text',
          title: 'Templates',
          subtitle: 'Manage content templates',
          type: 'link',
          onPress: () => router.push('/settings/templates'),
        },
      ],
    },
    {
      title: 'Subscription',
      items: [
        {
          id: 'plan',
          icon: 'diamond',
          title: 'Current Plan',
          subtitle: 'Pro • $29/month',
          type: 'link',
          onPress: () => router.push('/settings/subscription'),
        },
        {
          id: 'usage',
          icon: 'stats-chart',
          title: 'Usage',
          subtitle: '1,245 / 5,000 AI generations',
          type: 'link',
          onPress: () => router.push('/settings/usage'),
        },
        {
          id: 'billing',
          icon: 'card',
          title: 'Billing History',
          type: 'link',
          onPress: () => router.push('/settings/billing'),
        },
      ],
    },
    {
      title: 'Support',
      items: [
        {
          id: 'help',
          icon: 'help-circle',
          title: 'Help Center',
          type: 'link',
          onPress: () => router.push('/settings/help'),
        },
        {
          id: 'feedback',
          icon: 'chatbox-ellipses',
          title: 'Send Feedback',
          type: 'link',
          onPress: () => router.push('/settings/feedback'),
        },
        {
          id: 'about',
          icon: 'information-circle',
          title: 'About',
          subtitle: 'Version 1.0.0',
          type: 'link',
          onPress: () => router.push('/settings/about'),
        },
      ],
    },
    {
      title: '',
      items: [
        {
          id: 'signout',
          icon: 'log-out',
          title: 'Sign Out',
          type: 'action',
          onPress: handleSignOut,
        },
        {
          id: 'delete',
          icon: 'trash',
          title: 'Delete Account',
          type: 'action',
          danger: true,
          onPress: handleDeleteAccount,
        },
      ],
    },
  ];

  const renderSettingItem = useCallback(
    (item: SettingItem, isLast: boolean) => (
      <Pressable
        key={item.id}
        style={[
          styles.settingItem,
          !isLast && styles.settingItemBorder,
          { borderBottomColor: colors.border },
        ]}
        onPress={item.type !== 'toggle' ? item.onPress : undefined}
      >
        <View
          style={[
            styles.settingIcon,
            {
              backgroundColor: item.danger
                ? 'rgba(239, 68, 68, 0.2)'
                : colors.surfaceHover,
            },
          ]}
        >
          <Ionicons
            name={item.icon}
            size={20}
            color={item.danger ? '#EF4444' : colors.primary}
          />
        </View>

        <View style={styles.settingContent}>
          <Text
            style={[
              styles.settingTitle,
              { color: item.danger ? '#EF4444' : colors.text },
            ]}
          >
            {item.title}
          </Text>
          {item.subtitle && (
            <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
              {item.subtitle}
            </Text>
          )}
        </View>

        {item.type === 'toggle' && (
          <Switch
            value={item.value}
            onValueChange={item.onPress}
            trackColor={{ false: colors.surfaceHover, true: '#8B5CF6' }}
            thumbColor="#FFFFFF"
          />
        )}

        {item.type === 'link' && (
          <Ionicons
            name="chevron-forward"
            size={20}
            color={colors.textSecondary}
          />
        )}
      </Pressable>
    ),
    [colors]
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Settings',
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
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
        {sections.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.section}>
            {section.title && (
              <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>
                {section.title}
              </Text>
            )}
            <View style={[styles.sectionContent, { backgroundColor: colors.surface }]}>
              {section.items.map((item, itemIndex) =>
                renderSettingItem(item, itemIndex === section.items.length - 1)
              )}
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    gap: 24,
  },
  section: {
    gap: 8,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 4,
  },
  sectionContent: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 12,
  },
  settingItemBorder: {
    borderBottomWidth: 1,
  },
  settingIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
});
