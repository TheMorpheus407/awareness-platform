import React, { useState, useEffect } from 'react';
import { Mail, Bell, Shield, BookOpen, Tag, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Skeleton } from '../ui/skeleton';
import { toast } from 'react-hot-toast';
import { emailCampaignService } from '../../services/emailCampaignService';
import type { EmailPreferences, EmailFrequency } from '../../types/emailCampaign';

const emailCategories = [
  {
    key: 'marketing_emails',
    label: 'Marketing & Promotions',
    description: 'Special offers, new features, and product updates',
    icon: Tag,
  },
  {
    key: 'course_updates',
    label: 'Course Updates',
    description: 'New courses, updates to enrolled courses, and recommendations',
    icon: BookOpen,
  },
  {
    key: 'security_alerts',
    label: 'Security Alerts',
    description: 'Important security notifications and account activity',
    icon: Shield,
    required: true,
  },
  {
    key: 'newsletter',
    label: 'Newsletter',
    description: 'Weekly digest of cybersecurity news and tips',
    icon: Mail,
  },
  {
    key: 'promotional',
    label: 'Promotional Offers',
    description: 'Discounts, special events, and limited-time offers',
    icon: Bell,
  },
];

const frequencyOptions = [
  { value: EmailFrequency.IMMEDIATELY, label: 'Immediately' },
  { value: EmailFrequency.DAILY, label: 'Daily Digest' },
  { value: EmailFrequency.WEEKLY, label: 'Weekly Digest' },
  { value: EmailFrequency.MONTHLY, label: 'Monthly Summary' },
];

const weekDays = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

export const EmailPreferencesComponent: React.FC = () => {
  const [preferences, setPreferences] = useState<EmailPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const data = await emailCampaignService.getPreferences();
      setPreferences(data);
    } catch (error) {
      console.error('Failed to load email preferences:', error);
      toast.error('Failed to load email preferences');
    } finally {
      setLoading(false);
    }
  };

  const updatePreference = async (key: string, value: any) => {
    if (!preferences) return;

    try {
      setSaving(true);
      const updates = { [key]: value };
      const updated = await emailCampaignService.updatePreferences(updates);
      setPreferences(updated);
      toast.success('Preferences updated');
    } catch (error) {
      console.error('Failed to update preferences:', error);
      toast.error('Failed to update preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleUnsubscribeAll = async () => {
    if (!preferences) return;

    try {
      setSaving(true);
      const updated = await emailCampaignService.updatePreferences({
        is_subscribed: false,
      });
      setPreferences(updated);
      toast.success('You have been unsubscribed from all emails');
    } catch (error) {
      console.error('Failed to unsubscribe:', error);
      toast.error('Failed to unsubscribe');
    } finally {
      setSaving(false);
    }
  };

  const handleResubscribe = async () => {
    if (!preferences) return;

    try {
      setSaving(true);
      const updated = await emailCampaignService.updatePreferences({
        is_subscribed: true,
      });
      setPreferences(updated);
      toast.success('You have been resubscribed to emails');
    } catch (error) {
      console.error('Failed to resubscribe:', error);
      toast.error('Failed to resubscribe');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Card>
          <CardContent className="space-y-4 pt-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-64" />
                </div>
                <Skeleton className="h-6 w-12" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!preferences) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <p className="text-muted-foreground">Failed to load preferences</p>
          <Button onClick={loadPreferences} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Email Preferences</h1>
        <p className="text-muted-foreground">
          Manage your email notification settings
        </p>
      </div>

      {!preferences.is_subscribed && (
        <Card className="border-warning">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">You are unsubscribed from all emails</p>
                <p className="text-sm text-muted-foreground">
                  You will not receive any emails except for critical security alerts
                </p>
              </div>
              <Button onClick={handleResubscribe} disabled={saving}>
                Resubscribe
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Email Categories</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {emailCategories.map((category) => {
            const Icon = category.icon;
            const isEnabled = preferences[category.key as keyof EmailPreferences] as boolean;

            return (
              <div
                key={category.key}
                className="flex items-center justify-between space-x-4"
              >
                <div className="flex items-start space-x-3">
                  <Icon className="w-5 h-5 mt-0.5 text-muted-foreground" />
                  <div className="space-y-0.5">
                    <Label
                      htmlFor={category.key}
                      className="text-base font-medium"
                    >
                      {category.label}
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      {category.description}
                    </p>
                    {category.required && (
                      <p className="text-xs text-warning">
                        Required for account security
                      </p>
                    )}
                  </div>
                </div>
                <Switch
                  id={category.key}
                  checked={isEnabled}
                  onCheckedChange={(checked) =>
                    updatePreference(category.key, checked)
                  }
                  disabled={
                    saving ||
                    !preferences.is_subscribed ||
                    category.required
                  }
                />
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Email Frequency</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="frequency">How often would you like to receive emails?</Label>
            <Select
              value={preferences.email_frequency}
              onValueChange={(value) =>
                updatePreference('email_frequency', value)
              }
              disabled={saving || !preferences.is_subscribed}
            >
              <SelectTrigger id="frequency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {frequencyOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {preferences.email_frequency === EmailFrequency.WEEKLY && (
            <div className="space-y-2">
              <Label htmlFor="digest-day">Preferred day for weekly digest</Label>
              <Select
                value={String(preferences.digest_day || 1)}
                onValueChange={(value) =>
                  updatePreference('digest_day', parseInt(value))
                }
                disabled={saving || !preferences.is_subscribed}
              >
                <SelectTrigger id="digest-day">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {weekDays.map((day) => (
                    <SelectItem key={day.value} value={String(day.value)}>
                      {day.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {(preferences.email_frequency === EmailFrequency.DAILY ||
            preferences.email_frequency === EmailFrequency.WEEKLY) && (
            <div className="space-y-2">
              <Label htmlFor="digest-hour">Preferred time</Label>
              <Select
                value={String(preferences.digest_hour || 9)}
                onValueChange={(value) =>
                  updatePreference('digest_hour', parseInt(value))
                }
                disabled={saving || !preferences.is_subscribed}
              >
                <SelectTrigger id="digest-hour">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 24 }, (_, i) => (
                    <SelectItem key={i} value={String(i)}>
                      {i.toString().padStart(2, '0')}:00
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {preferences.is_subscribed && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-destructive">Unsubscribe from all emails</h3>
                <p className="text-sm text-muted-foreground">
                  You will stop receiving all emails except critical security alerts
                </p>
              </div>
              <Button
                variant="danger"
                onClick={handleUnsubscribeAll}
                disabled={saving}
              >
                Unsubscribe from All
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};