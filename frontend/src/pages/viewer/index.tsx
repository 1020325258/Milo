import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { client } from '@/api/client';

export function ViewerPage() {
	const { docId } = useParams<{ docId: string }>();
	const [content, setContent] = useState<string>('');
	const [filename, setFilename] = useState<string>('');
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string>('');

	useEffect(() => {
		if (!docId) return;

		const fetchData = async () => {
			setLoading(true);
			try {
				// 获取文档信息
				try {
					const info = await client.get<{ filename: string }>(`/api/document/${docId}`);
					setFilename(info.filename);
				} catch {
					// ignore
				}

				// 获取文档内容（纯文本，需要直接 fetch）
				const { getUserId } = await import('@/api/client');
				const res = await fetch(`/api/document/${docId}/content`, {
					headers: { 'X-User-ID': getUserId() },
				});
				if (!res.ok) {
					setError('加载失败');
					return;
				}
				const text = await res.text();
				setContent(text);
			} catch {
				setError('加载失败');
			} finally {
				setLoading(false);
			}
		};

		fetchData();
	}, [docId]);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-screen text-muted-foreground">
				加载中...
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex items-center justify-center h-screen text-destructive">
				{error}
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-background">
			<div className="max-w-4xl mx-auto px-6 py-8">
				<h1 className="text-lg font-semibold mb-6 text-foreground border-b pb-4">
					{filename}
				</h1>
				<div className="prose prose-sm max-w-none">
					<ReactMarkdown remarkPlugins={[remarkGfm]}>
						{content}
					</ReactMarkdown>
				</div>
			</div>
		</div>
	);
}
