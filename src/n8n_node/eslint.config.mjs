import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: ['build/**', 'dist/**', 'node_modules/**'],
  },
  ...tseslint.configs.recommended,
  {
    files: ['index.ts', 'credentials/**/*.ts', 'nodes/**/*.ts', 'transport/**/*.ts'],
    rules: {
      complexity: ['error', 16],
    },
  },
);
