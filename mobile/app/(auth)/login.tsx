/**
 * Login Screen
 *
 * Social login only - TikTok-simple onboarding.
 */

import { useState } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';

import { useTheme } from '@/lib/theme';
import { useAuth } from '@/lib/auth';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const { signIn } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      // In production, implement Google OAuth
      // For now, simulate login
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Mock user data
      await signIn('mock-token', {
        id: '1',
        email: 'user@example.com',
        display_name: 'Demo User',
        username: 'demouser',
      });
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAppleLogin = async () => {
    setIsLoading(true);
    try {
      // In production, implement Apple Sign In
      await new Promise((resolve) => setTimeout(resolve, 1500));

      await signIn('mock-token', {
        id: '1',
        email: 'user@example.com',
        display_name: 'Demo User',
        username: 'demouser',
      });
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.background,
          paddingTop: insets.top,
          paddingBottom: insets.bottom,
        },
      ]}
    >
      {/* Logo & Title */}
      <View style={styles.header}>
        <View style={[styles.logo, { backgroundColor: colors.primary }]}>
          <Text style={styles.logoText}>ID</Text>
        </View>
        <Text style={[styles.title, { color: colors.text }]}>IDKit</Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
          Your AI-powered influencer toolkit
        </Text>
      </View>

      {/* Login Buttons */}
      <View style={styles.buttons}>
        <Pressable
          style={[styles.button, styles.googleButton]}
          onPress={handleGoogleLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <>
              <Ionicons name="logo-google" size={20} color="#000" />
              <Text style={styles.googleButtonText}>Continue with Google</Text>
            </>
          )}
        </Pressable>

        <Pressable
          style={[styles.button, styles.appleButton]}
          onPress={handleAppleLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Ionicons name="logo-apple" size={22} color="#FFF" />
              <Text style={styles.appleButtonText}>Continue with Apple</Text>
            </>
          )}
        </Pressable>
      </View>

      {/* Terms */}
      <View style={styles.terms}>
        <Text style={[styles.termsText, { color: colors.textSecondary }]}>
          By continuing, you agree to our{' '}
          <Text style={styles.link}>Terms of Service</Text> and{' '}
          <Text style={styles.link}>Privacy Policy</Text>
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 60,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  logoText: {
    color: '#FFF',
    fontSize: 32,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  buttons: {
    width: '100%',
    maxWidth: 340,
    gap: 12,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 12,
  },
  googleButton: {
    backgroundColor: '#FFF',
  },
  googleButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
  appleButton: {
    backgroundColor: '#000',
    borderWidth: 1,
    borderColor: '#333',
  },
  appleButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  terms: {
    position: 'absolute',
    bottom: 40,
    left: 24,
    right: 24,
  },
  termsText: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  link: {
    textDecorationLine: 'underline',
  },
});
