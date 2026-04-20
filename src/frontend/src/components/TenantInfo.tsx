import { useEffect, useState } from 'react';

interface Tenant {
  id: number;
  name: string;
  slug: string;
  quota_tasks: number;
  quota_storage_mb: number;
  quota_api_calls: number;
  is_active: boolean;
}

interface TenantInfoProps {
  apiKey: string;
}

function TenantInfo({ apiKey }: TenantInfoProps) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!apiKey) {
      setError('请先登录');
      setLoading(false);
      return;
    }

    fetch('/api/v1/tenants/me', {
      headers: {
        'X-API-Key': apiKey
      }
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Unauthorized');
        }
        return res.json();
      })
      .then(data => {
        setTenant(data);
        setLoading(false);
      })
      .catch(err => {
        setError('无租户信息');
        setLoading(false);
      });
  }, [apiKey]);

  if (loading) {
    return (
      <div className="px-3 py-2 text-slate-400 text-sm">
        加载中...
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-3 py-2 text-red-400 text-sm">
        {error}
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="px-3 py-2 text-slate-400 text-sm">
        无租户信息
      </div>
    );
  }

  return (
    <div className="px-3 py-2 bg-slate-800/50 rounded-lg border border-cyan-500/30">
      <div className="text-cyan-400 font-medium text-sm">
        {tenant.name}
      </div>
      <div className="text-slate-400 text-xs mt-1">
        配额: {tenant.quota_tasks} 任务 | {tenant.quota_storage_mb} MB 存储
      </div>
    </div>
  );
}

export default TenantInfo;