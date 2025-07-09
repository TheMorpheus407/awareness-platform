import React from 'react';
import { motion } from 'framer-motion';

interface LoadingSkeletonProps {
  className?: string;
  count?: number;
  height?: string;
  width?: string;
  circle?: boolean;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className = '',
  count = 1,
  height = 'h-4',
  width = 'w-full',
  circle = false
}) => {
  const skeletons = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {skeletons.map((index) => (
        <motion.div
          key={index}
          className={`${width} ${height} ${circle ? 'rounded-full' : 'rounded'} bg-gray-200 dark:bg-gray-700 ${className}`}
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </>
  );
};

export const LoadingCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <LoadingSkeleton width="w-32" height="h-6" />
        <LoadingSkeleton width="w-16" height="h-8" />
      </div>
      <LoadingSkeleton count={3} className="mb-2" />
      <div className="mt-4 flex gap-2">
        <LoadingSkeleton width="w-20" height="h-8" />
        <LoadingSkeleton width="w-20" height="h-8" />
      </div>
    </div>
  );
};

export const LoadingTable: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <LoadingSkeleton width="w-48" height="h-6" />
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="p-4 flex items-center gap-4">
            <LoadingSkeleton circle width="w-10" height="h-10" />
            <div className="flex-1">
              <LoadingSkeleton width="w-32" height="h-4" className="mb-1" />
              <LoadingSkeleton width="w-24" height="h-3" />
            </div>
            <LoadingSkeleton width="w-20" height="h-8" />
          </div>
        ))}
      </div>
    </div>
  );
};