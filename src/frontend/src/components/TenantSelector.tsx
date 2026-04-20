import { useEffect, useState } from 'react';

interface Tenant {
  id: number;
  name: string;
  slug: string;
}

interface TenantSelectorProps {
  apiKey: string;
  onTenantChange?: (tenantId: number) => void;
}

function TenantSelector({ apiKey, onTenantChange }: TenantSelectorProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/tenants', {
      headers: {
        'X-API-Key': apiKey
      }
    })
      .then(res => res.json())
      .then(data => {
        setTenants(data);
        if (data.length > 0) {
          setSelectedTenant(data[0]);
        }
        setLoading(false);
      })
      .catch(err => {
        setLoading(false);
      });
  }, [apiKey]);

  const handleTenantClick = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setIsOpen(false);
    if (onTenantChange) {
      onTenantChange(tenant.id);
    }
    // 更新 localStorage
    localStorage.setItem('tenant_id', String(tenant.id));
  };

  if (loading) {
    return (
      <div className="px-3 py-2 text-slate-400 text-sm">
        加载中...
      </div>
    );
  }

  // 只有一个租户时，只显示信息
  if (tenants.length <= 1) {
    return (
      <div className="px-3 py-2 bg-slate-800/50 rounded-lg border border-cyan-500/30">
        <div className="text-cyan-400 font-medium text-sm">
          {selectedTenant?.name || '默认租户'}
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 bg-slate-800/50 rounded-lg border border-cyan-500/30 hover:border-cyan-500/50 transition-colors w-full text-left"
      >
        <div className="text-cyan-400 font-medium text-sm">
          {selectedTenant?.name || '选择租户'}
        </div>
        <div className="text-slate-400 text-xs mt-1">
          ▼ 切换租户
        </div>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-slate-800 rounded-lg border border-cyan-500/30 w-full z-50">
          {tenants.map(tenant => (
            <div
              key={tenant.id}
              onClick={() => handleTenantClick(tenant)}
              className={`px-3 py-2 cursor-pointer hover:bg-slate-700 ${
                selectedTenant?.id === tenant.id ? 'bg-cyan-500/20' : ''
              }`}
            >
              <div className="text-cyan-400 font-medium text-sm">
                {tenant.name}
              </div>
              <div className="text-slate-400 text-xs">
                {tenant.slug}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TenantSelector;