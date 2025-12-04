import React from 'react';

export function Label({ children, className = '' }) {
  const baseClasses = "block text-sm font-medium text-gray-700 mb-1";
  const finalClasses = className ? baseClasses + " " + className : baseClasses;
  return (
    <label className={finalClasses}>
      {children}
    </label>
  );
}

export default Label;
