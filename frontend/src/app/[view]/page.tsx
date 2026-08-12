import Home from '../page';

export function generateStaticParams() {
  return [
    { view: 'sessions' },
    { view: 'overview' },
    { view: 'timeline' },
    { view: 'tree' },
    { view: 'logs' },
    { view: 'metrics' },
  ];
}

export const dynamicParams = false;

export default function ViewPage() {
  return <Home />;
}
