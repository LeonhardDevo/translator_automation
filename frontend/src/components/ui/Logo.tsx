import React from 'react';

interface LogoProps {
  width?: number;
  height?: number;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ width = 100, height = 100, className = '' }) => {
  return (
    <img 
      src="/logo.png" 
      alt="LangWay" 
      width={width} 
      height={height}
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default Logo;
