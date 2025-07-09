import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Save,
  Send,
  Calendar,
  Users,
  FileText,
  Settings,
  Eye,
  TestTube,
  ChevronLeft,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Badge } from '../ui/Badge';
import { Skeleton } from '../ui/skeleton';
import { toast } from 'react-hot-toast';
import { emailCampaignService } from '../../services/emailCampaignService';
import type {
  Campaign,
  CampaignCreate,
  CampaignUpdate,
  EmailTemplate,
} from '../../types/emailCampaign';
import type { User } from '../../types/api';

const userRoles = [
  { value: 'user', label: 'User' },
  { value: 'company_admin', label: 'Company Admin' },
  { value: 'admin', label: 'Admin' },
];

const campaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required'),
  description: z.string().optional(),
  template_id: z.string().min(1, 'Template is required'),
  scheduled_at: z.string().optional(),
  target_all_users: z.boolean(),
  target_user_roles: z.array(z.string()),
  exclude_unsubscribed: z.boolean(),
  custom_subject: z.string().optional(),
  custom_preview_text: z.string().optional(),
});

type CampaignFormData = z.infer<typeof campaignSchema>;

export const EmailCampaignEditor: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = !!id;

  const [loading, setLoading] = useState(false);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<CampaignFormData>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      target_all_users: true,
      target_user_roles: [],
      exclude_unsubscribed: true,
    },
  });

  const templateId = watch('template_id');

  useEffect(() => {
    loadTemplates();
    if (isEditing) {
      loadCampaign();
    }
  }, [id]);

  useEffect(() => {
    if (templateId) {
      const template = templates.find((t) => t.id === templateId);
      setSelectedTemplate(template || null);
    }
  }, [templateId, templates]);

  const loadTemplates = async () => {
    try {
      const data = await emailCampaignService.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast.error('Failed to load email templates');
    }
  };

  const loadCampaign = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await emailCampaignService.getCampaign(id);
      setCampaign(data);

      // Set form values
      setValue('name', data.name);
      setValue('description', data.description || '');
      setValue('template_id', data.template_id);
      setValue('scheduled_at', data.scheduled_at || '');
      setValue('target_all_users', data.target_all_users);
      setValue('target_user_roles', data.target_user_roles);
      setValue('exclude_unsubscribed', data.exclude_unsubscribed);
      setValue('custom_subject', data.custom_subject || '');
      setValue('custom_preview_text', data.custom_preview_text || '');
    } catch (error) {
      console.error('Failed to load campaign:', error);
      toast.error('Failed to load campaign');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: CampaignFormData) => {
    try {
      setLoading(true);

      if (isEditing) {
        await emailCampaignService.updateCampaign(id!, data as CampaignUpdate);
        toast.success('Campaign updated successfully');
      } else {
        const created = await emailCampaignService.createCampaign(
          data as CampaignCreate
        );
        toast.success('Campaign created successfully');
        navigate(`/admin/email-campaigns/${created.id}`);
      }
    } catch (error) {
      console.error('Failed to save campaign:', error);
      toast.error('Failed to save campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleSendTest = async () => {
    if (!selectedTemplate || !testEmail) return;

    try {
      setSendingTest(true);
      await emailCampaignService.testTemplate(
        selectedTemplate.id,
        testEmail,
        {}
      );
      toast.success('Test email sent successfully');
      setShowTestDialog(false);
      setTestEmail('');
    } catch (error) {
      console.error('Failed to send test email:', error);
      toast.error('Failed to send test email');
    } finally {
      setSendingTest(false);
    }
  };

  const handleSendCampaign = async () => {
    if (!campaign) return;

    try {
      setLoading(true);
      await emailCampaignService.sendCampaign(campaign.id, {
        send_immediately: true,
      });
      toast.success('Campaign sent successfully');
      navigate('/admin/email-campaigns');
    } catch (error) {
      console.error('Failed to send campaign:', error);
      toast.error('Failed to send campaign');
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEditing) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-1/3" />
        <Card>
          <CardContent className="space-y-4 pt-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/admin/email-campaigns')}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">
            {isEditing ? 'Edit Campaign' : 'Create Campaign'}
          </h1>
          <p className="text-muted-foreground">
            Design and configure your email campaign
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Tabs defaultValue="details" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="details">
              <FileText className="w-4 h-4 mr-2" />
              Details
            </TabsTrigger>
            <TabsTrigger value="audience">
              <Users className="w-4 h-4 mr-2" />
              Audience
            </TabsTrigger>
            <TabsTrigger value="preview">
              <Eye className="w-4 h-4 mr-2" />
              Preview
            </TabsTrigger>
            <TabsTrigger value="schedule">
              <Calendar className="w-4 h-4 mr-2" />
              Schedule
            </TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Campaign Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Campaign Name</Label>
                  <Input
                    id="name"
                    {...register('name')}
                    placeholder="Enter campaign name"
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive">
                      {errors.name.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    {...register('description')}
                    placeholder="Describe your campaign"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="template_id">Email Template</Label>
                  <Select
                    value={watch('template_id')}
                    onValueChange={(value) => setValue('template_id', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a template" />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.map((template) => (
                        <SelectItem key={template.id} value={template.id}>
                          <div className="flex items-center justify-between w-full">
                            <span>{template.name}</span>
                            <Badge variant="outline" className="ml-2">
                              {template.type}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.template_id && (
                    <p className="text-sm text-destructive">
                      {errors.template_id.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="custom_subject">Custom Subject (Optional)</Label>
                  <Input
                    id="custom_subject"
                    {...register('custom_subject')}
                    placeholder="Override template subject"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="custom_preview_text">
                    Preview Text (Optional)
                  </Label>
                  <Input
                    id="custom_preview_text"
                    {...register('custom_preview_text')}
                    placeholder="Text shown in email preview"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="audience" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Target Audience</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="target_all_users">Send to All Users</Label>
                    <p className="text-sm text-muted-foreground">
                      Send this campaign to all active users
                    </p>
                  </div>
                  <Switch
                    id="target_all_users"
                    checked={watch('target_all_users')}
                    onCheckedChange={(checked) =>
                      setValue('target_all_users', checked)
                    }
                  />
                </div>

                {!watch('target_all_users') && (
                  <div className="space-y-2">
                    <Label>Target User Roles</Label>
                    <div className="space-y-2">
                      {userRoles.map((role) => (
                        <label
                          key={role.value}
                          className="flex items-center space-x-2"
                        >
                          <input
                            type="checkbox"
                            value={role.value}
                            checked={watch('target_user_roles').includes(
                              role.value
                            )}
                            onChange={(e) => {
                              const roles = watch('target_user_roles');
                              if (e.target.checked) {
                                setValue('target_user_roles', [
                                  ...roles,
                                  role.value,
                                ]);
                              } else {
                                setValue(
                                  'target_user_roles',
                                  roles.filter((r) => r !== role.value)
                                );
                              }
                            }}
                          />
                          <span>{role.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="exclude_unsubscribed">
                      Exclude Unsubscribed Users
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Don't send to users who have unsubscribed
                    </p>
                  </div>
                  <Switch
                    id="exclude_unsubscribed"
                    checked={watch('exclude_unsubscribed')}
                    onCheckedChange={(checked) =>
                      setValue('exclude_unsubscribed', checked)
                    }
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Email Preview</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedTemplate ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div className="flex space-x-2">
                        <Button
                          type="button"
                          variant={previewMode === 'desktop' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setPreviewMode('desktop')}
                        >
                          Desktop
                        </Button>
                        <Button
                          type="button"
                          variant={previewMode === 'mobile' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setPreviewMode('mobile')}
                        >
                          Mobile
                        </Button>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setShowTestDialog(true)}
                      >
                        <TestTube className="w-4 h-4 mr-2" />
                        Send Test
                      </Button>
                    </div>

                    <div
                      className={`border rounded-lg p-4 ${
                        previewMode === 'mobile' ? 'max-w-sm mx-auto' : ''
                      }`}
                    >
                      <div className="space-y-2 mb-4">
                        <p className="text-sm text-muted-foreground">Subject:</p>
                        <p className="font-medium">
                          {watch('custom_subject') || selectedTemplate.subject}
                        </p>
                      </div>
                      <div className="border-t pt-4">
                        <iframe
                          srcDoc={selectedTemplate.html_content}
                          className="w-full h-96 border-0"
                          title="Email Preview"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    Select a template to preview
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="schedule" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Send Schedule</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="scheduled_at">Schedule For Later</Label>
                  <Input
                    id="scheduled_at"
                    type="datetime-local"
                    {...register('scheduled_at')}
                  />
                  <p className="text-sm text-muted-foreground">
                    Leave empty to save as draft
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end space-x-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/email-campaigns')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="w-4 h-4 mr-2" />
            {isEditing ? 'Update Campaign' : 'Create Campaign'}
          </Button>
          {campaign && campaign.status === 'draft' && (
            <Button
              type="button"
              variant="default"
              onClick={handleSendCampaign}
              disabled={loading}
            >
              <Send className="w-4 h-4 mr-2" />
              Send Now
            </Button>
          )}
        </div>
      </form>

      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Test Email</DialogTitle>
            <DialogDescription>
              Send a test email to preview how it will look in an inbox
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="test-email">Email Address</Label>
              <Input
                id="test-email"
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="Enter email address"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowTestDialog(false)}
              disabled={sendingTest}
            >
              Cancel
            </Button>
            <Button onClick={handleSendTest} disabled={!testEmail || sendingTest}>
              <Send className="w-4 h-4 mr-2" />
              Send Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};