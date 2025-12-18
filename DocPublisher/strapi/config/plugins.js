module.exports = ({ env }) => ({
  // Users & Permissions plugin
  'users-permissions': {
    config: {
      jwtSecret: env('JWT_SECRET', 'jzc-dev-shared-secret-key-2025'),
    },
  },
  // CKEditor 5 plugin
  ckeditor: {
    enabled: true,
  },
});
