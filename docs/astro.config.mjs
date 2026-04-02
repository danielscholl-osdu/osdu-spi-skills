// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: 'https://danielscholl-osdu.github.io',
	base: '/osdu-spi-skills',
	integrations: [
		starlight({
			title: 'OSDU SPI Skills',
			description: 'Unified AI agent skills for the OSDU platform — deploys to Copilot, Claude, Cursor via APM',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/danielscholl-osdu/osdu-spi-skills' }],
			editLink: {
				baseUrl: 'https://github.com/danielscholl-osdu/osdu-spi-skills/edit/main/docs/',
			},
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'First Session', slug: 'getting-started/first-session' },
					],
				},
				{
					label: 'AI System',
					items: [
						{ label: 'Architecture', slug: 'system/architecture' },
						{ label: 'Agents', slug: 'system/agents' },
						{ label: 'Skills', slug: 'system/skills' },
						{ label: 'Commands', slug: 'system/commands' },
					],
				},
				{
					label: 'Platform Guide',
					items: [
						{ label: 'APM Integration', slug: 'platform/apm' },
						{ label: 'Copilot', slug: 'platform/copilot' },
						{ label: 'Claude Code', slug: 'platform/claude' },
						{ label: 'Cursor & Others', slug: 'platform/cursor' },
					],
				},
				{
					label: 'Development',
					items: [
						{ label: 'Contributing', slug: 'development/contributing' },
						{ label: 'Testing', slug: 'development/testing' },
						{ label: 'Adding Skills', slug: 'development/adding-skills' },
					],
				},
			],
		}),
	],
});
