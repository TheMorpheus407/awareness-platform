import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  ChevronLeft,
  Mail,
  Eye,
  MousePointer,
  TrendingUp,
  Users,
  Clock,
  AlertCircle,
  Monitor,
  Smartphone,
  Tablet,
  Link2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { emailCampaignService } from '@/services/emailCampaignService';
import { CampaignStats } from '@/types/emailCampaign';
import { formatDate, formatPercentage } from '@/lib/utils';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: number;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
}) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <Icon className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      )}
      {trend !== undefined && (
        <div className="flex items-center mt-2">
          <TrendingUp
            className={`h-4 w-4 mr-1 ${
              trend >= 0 ? 'text-success' : 'text-destructive'
            }`}
          />
          <span
            className={`text-xs ${
              trend >= 0 ? 'text-success' : 'text-destructive'
            }`}
          >
            {trend >= 0 ? '+' : ''}
            {trend}%
          </span>
        </div>
      )}
    </CardContent>
  </Card>
);

export const EmailCampaignStats: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadStats();
    }
  }, [id]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await emailCampaignService.getCampaignStats(id!);
      setStats(data);
    } catch (error) {
      console.error('Failed to load campaign stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHourlyData = () => {
    if (!stats) return [];

    const hours = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      opens: stats.opens_by_hour[i] || 0,
      clicks: stats.clicks_by_hour[i] || 0,
    }));

    return hours;
  };

  const getDeviceData = () => {
    if (!stats) return [];

    const devices = Object.entries(stats.opens_by_device).map(([device, opens]) => ({
      device: device.charAt(0).toUpperCase() + device.slice(1),
      opens,
      clicks: stats.clicks_by_device[device] || 0,
    }));

    return devices;
  };

  const getFunnelData = () => {
    if (!stats) return [];

    return [
      { stage: 'Sent', value: stats.total_sent, percentage: 100 },
      {
        stage: 'Delivered',
        value: stats.total_delivered,
        percentage: stats.delivery_rate,
      },
      {
        stage: 'Opened',
        value: stats.total_opened,
        percentage: stats.open_rate,
      },
      {
        stage: 'Clicked',
        value: stats.total_clicked,
        percentage: stats.click_rate,
      },
    ];
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-1/3" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No statistics available</h3>
          <p className="text-muted-foreground">
            Campaign statistics will appear here once the campaign is sent
          </p>
          <Button onClick={() => navigate(-1)} className="mt-4">
            Go Back
          </Button>
        </CardContent>
      </Card>
    );
  }

  const deviceIcons = {
    desktop: Monitor,
    mobile: Smartphone,
    tablet: Tablet,
  };

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
          <h1 className="text-3xl font-bold">{stats.name}</h1>
          <p className="text-muted-foreground">
            Campaign statistics and performance
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Recipients"
          value={stats.total_recipients.toLocaleString()}
          icon={Users}
        />
        <StatCard
          title="Delivery Rate"
          value={formatPercentage(stats.delivery_rate)}
          subtitle={`${stats.total_delivered.toLocaleString()} delivered`}
          icon={Mail}
        />
        <StatCard
          title="Open Rate"
          value={formatPercentage(stats.open_rate)}
          subtitle={`${stats.total_opened.toLocaleString()} opens`}
          icon={Eye}
        />
        <StatCard
          title="Click Rate"
          value={formatPercentage(stats.click_rate)}
          subtitle={`${stats.total_clicked.toLocaleString()} clicks`}
          icon={MousePointer}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Engagement Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getHourlyData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="opens"
                  stroke="#3b82f6"
                  name="Opens"
                />
                <Line
                  type="monotone"
                  dataKey="clicks"
                  stroke="#10b981"
                  name="Clicks"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Engagement by Device</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDeviceData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="device" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="opens" fill="#3b82f6" name="Opens" />
                <Bar dataKey="clicks" fill="#10b981" name="Clicks" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Email Funnel</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={getFunnelData()}
              layout="horizontal"
              margin={{ left: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="stage" type="category" />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6">
                {getFunnelData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {stats.link_clicks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Link Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Link URL</TableHead>
                  <TableHead className="text-right">Total Clicks</TableHead>
                  <TableHead className="text-right">Unique Clicks</TableHead>
                  <TableHead className="text-right">CTR</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.link_clicks.map((link, index) => (
                  <TableRow key={index}>
                    <TableCell className="flex items-center space-x-2">
                      <Link2 className="w-4 h-4 text-muted-foreground" />
                      <span className="truncate max-w-md">{link.url}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      {link.clicks.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {link.unique_clicks.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatPercentage(
                        (link.unique_clicks / stats.total_delivered) * 100
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bounce Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercentage(stats.bounce_rate)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.total_bounced.toLocaleString()} bounced
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unsubscribe Rate</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercentage(stats.unsubscribe_rate)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.total_unsubscribed.toLocaleString()} unsubscribed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Send Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">
              {stats.sent_at ? formatDate(stats.sent_at) : 'Not sent'}
            </div>
            {stats.completed_at && (
              <p className="text-xs text-muted-foreground mt-1">
                Completed: {formatDate(stats.completed_at)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};