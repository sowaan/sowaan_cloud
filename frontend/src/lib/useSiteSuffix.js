import { useEffect, useState } from 'react';
import { apiFetch } from './api';

const FALLBACK = 'sowaan.cloud';

export function useSiteSuffix() {
  const [suffix, setSuffix] = useState(FALLBACK);

  useEffect(() => {
    apiFetch(
      '/api/method/sowaan_cloud.sowaan_cloud.doctype.cloud_settings.cloud_settings.get_site_suffix'
    )
      .then((r) => r.json())
      .then((data) => {
        const value = data?.message;
        if (value && typeof value === 'string') setSuffix(value);
      })
      .catch(() => {});
  }, []);

  return suffix;
}
