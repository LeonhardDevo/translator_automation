import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const UserDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState<{ submitted: number; translated: number }>({ submitted: 0, translated: 0 });

  useEffect(() => {
    axios.get('/user/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
      .then(resp => setStats(resp.data));
  }, []);

  return (
    <div>
      {/* <LanguageSwitcher /> */}
      <h2>{t('welcome', { name: 'User' })}</h2>
      <p>{t('user_stats', { count: stats.submitted, translated: stats.translated })}</p>
    </div>
  );
};

export default UserDashboard;
