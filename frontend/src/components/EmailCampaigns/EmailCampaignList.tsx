import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mail,
  Plus,
  Send,
  Clock,
  CheckCircle,
  XCircle,
  BarChart3,
  Users,
  Eye,
  MousePointer,
  TrendingUp,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { emailCampaignService } from '@/services/emailCampaignService';
import { Campaign, CampaignStatus } from '@/types/emailCampaign';
import { formatDate, formatPercentage } from '@/lib/utils';

const statusConfig = {
  draft: { label: 'Draft', color: 'secondary', icon: Mail },
  scheduled: { label: 'Scheduled', color: 'info', icon: Clock },
  sending: { label: 'Sending', color: 'warning', icon: Send },
  sent: { label: 'Sent', color: 'success', icon: CheckCircle },
  paused: { label: 'Paused', color: 'warning', icon: Clock },
  cancelled: { label: 'Cancelled', color: 'destructive', icon: XCircle },
  completed: { label: 'Completed', color: 'success', icon: CheckCircle },
};

export const EmailCampaignList: React.FC = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | 'all'>('all');

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const data = await emailCampaignService.getCampaigns(
        statusFilter === 'all' ? undefined : statusFilter
      );
      setCampaigns(data);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendCampaign = async (campaignId: string) => {
    try {
      await emailCampaignService.sendCampaign(campaignId, {
        send_immediately: true,
      });
      await loadCampaigns();
    } catch (error) {
      console.error('Failed to send campaign:', error);
    }
  };

  const renderCampaignStats = (campaign: Campaign) => {
    const stats = [
      {
        icon: Users,
        label: 'Recipients',
        value: campaign.total_recipients.toLocaleString(),
      },
      {
        icon: Eye,
        label: 'Opens',
        value: `${campaign.total_opened.toLocaleString()} (${formatPercentage(
          campaign.open_rate
        )})`,
      },
      {
        icon: MousePointer,
        label: 'Clicks',
        value: `${campaign.total_clicked.toLocaleString()} (${formatPercentage(
          campaign.click_rate
        )})`,
      },
      {
        icon: TrendingUp,
        label: 'Delivered',
        value: `${campaign.total_delivered.toLocaleString()} (${formatPercentage(
          campaign.delivery_rate
        )})`,
      },
    ];

    return (
      <div className="grid grid-cols-4 gap-4 mt-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="flex items-center space-x-2">
              <Icon className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-sm font-medium">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-1/3" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-2/3" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Email Campaigns</h1>
          <p className="text-muted-foreground">
            Create and manage your email marketing campaigns
          </p>
        </div>
        <Button onClick={() => navigate('/admin/email-campaigns/new')}>
          <Plus className="w-4 h-4 mr-2" />
          Create Campaign
        </Button>
      </div>

      <div className="flex items-center space-x-4">
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as CampaignStatus | 'all')}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Campaigns</SelectItem>
            {Object.entries(statusConfig).map(([value, config]) => (
              <SelectItem key={value} value={value}>
                {config.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4">
        {campaigns.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Mail className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No campaigns yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first email campaign to engage with your users
              </p>
              <Button onClick={() => navigate('/admin/email-campaigns/new')}>
                <Plus className="w-4 h-4 mr-2" />
                Create Campaign
              </Button>
            </CardContent>
          </Card>
        ) : (
          campaigns.map((campaign) => {
            const status = statusConfig[campaign.status];
            const StatusIcon = status.icon;

            return (
              <Card
                key={campaign.id}
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => navigate(`/admin/email-campaigns/${campaign.id}`)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-xl">{campaign.name}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        {campaign.description}
                      </p>
                    </div>
                    <Badge variant={status.color as any}>
                      <StatusIcon className="w-3 h-3 mr-1" />
                      {status.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-center mb-4">
                    <div className="text-sm text-muted-foreground">
                      {campaign.scheduled_at && (
                        <span>Scheduled for {formatDate(campaign.scheduled_at)}</span>
                      )}
                      {campaign.sent_at && (
                        <span>Sent on {formatDate(campaign.sent_at)}</span>
                      )}
                      {campaign.status === 'draft' && (
                        <span>Created {formatDate(campaign.created_at)}</span>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      {campaign.status === 'draft' && (
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSendCampaign(campaign.id);
                          }}
                        >
                          <Send className="w-4 h-4 mr-2" />
                          Send Now
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/admin/email-campaigns/${campaign.id}/stats`);
                        }}
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        View Stats
                      </Button>
                    </div>
                  </div>
                  {campaign.total_recipients > 0 && renderCampaignStats(campaign)}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
};