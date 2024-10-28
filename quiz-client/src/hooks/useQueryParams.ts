import { useSearchParams } from 'react-router-dom';

export const useQueryParams = () => {
  const [searchParams] = useSearchParams();

  return {
    userId: searchParams.get('userId') || '',
    isAdmin: searchParams.get('role') === 'admin',
  };
};