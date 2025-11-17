import { Link, useLocation } from 'react-router-dom';

export default function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Green Agent', icon: '🌱', description: 'Full Demo' },
    { path: '/white-agent', label: 'White Agent', icon: '⚪', description: 'Reasoning Engine' },
  ];

  return (
    <nav className="bg-card border-b border-border shadow-sm">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex space-x-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  px-5 py-4 text-sm font-medium transition-all relative group
                  ${
                    isActive
                      ? 'text-primary border-b-2 border-primary bg-primary/5'
                      : 'text-muted-foreground hover:text-foreground border-b-2 border-transparent hover:bg-accent'
                  }
                `}
              >
                <span className="flex items-center gap-3">
                  <span className="text-xl">{item.icon}</span>
                  <div className="flex flex-col">
                    <span className="font-semibold">{item.label}</span>
                    <span className={`text-xs ${isActive ? 'text-primary/70' : 'text-muted-foreground'}`}>
                      {item.description}
                    </span>
                  </div>
                </span>
                {isActive && (
                  <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-primary via-white-agent to-primary" />
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

