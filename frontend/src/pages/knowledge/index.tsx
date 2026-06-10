import { useEffect, useState } from 'react';
import { Database, Plus, Trash2, FileText, RefreshCw, Eye, ChevronRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { client } from '@/api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface KnowledgeBase {
	id: number;
	name: string;
	description: string;
	embedding_model: string;
	document_count: number;
	chunk_count: number;
	created_at: string;
	updated_at: string;
}

interface Document {
	id: number;
	knowledge_base_id: number;
	filename: string;
	file_type: string;
	file_size: number;
	status: string;
	chunk_count: number;
	error_message: string | null;
	created_at: string;
}

interface Chunk {
	id: number;
	chunk_id: string;
	chunk_index: number;
	content: string;
	section_title: string | null;
}


// Pipeline 步骤定义
const PIPELINE_STEPS = [
	{ key: 'uploading', label: '上传文件' },
	{ key: 'parsing', label: '解析文档' },
	{ key: 'chunking', label: '智能分片' },
	{ key: 'embedding', label: '向量化' },
	{ key: 'indexing', label: '索引入库' },
];

export function KnowledgeBasePage() {
	const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
	const [loading, setLoading] = useState(false);
	const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
	const [documents, setDocuments] = useState<Document[]>([]);
	const [showCreate, setShowCreate] = useState(false);
	const [newName, setNewName] = useState('');
	const [newDesc, setNewDesc] = useState('');
	const [viewingDoc, setViewingDoc] = useState<Document | null>(null);
	const [chunks, setChunks] = useState<Chunk[]>([]);
	const [chunksLoading, setChunksLoading] = useState(false);
	// Pipeline 进度状态
	const [processingDocId, setProcessingDocId] = useState<number | null>(null);
	const [pipelineStep, setPipelineStep] = useState<number>(-1);

	const fetchKbs = async () => {
		setLoading(true);
		try {
			const data = await client.get<{ items: KnowledgeBase[] }>('/api/knowledge/', { page: '1', page_size: '100' });
			setKbs(data.items || []);
		} catch {
			toast.error('加载知识库失败');
		} finally {
			setLoading(false);
		}
	};

	const fetchDocs = async (kbId: number) => {
		try {
			const data = await client.get<{ items: Document[] }>('/api/document/', { knowledge_base_id: String(kbId), page: '1', page_size: '100' });
			setDocuments(data.items || []);
		} catch {
			toast.error('加载文档失败');
		}
	};

	const fetchChunks = async (doc: Document) => {
		setChunksLoading(true);
		setViewingDoc(doc);
		try {
			const data = await client.get<{ chunks: Chunk[] }>(`/api/document/${doc.id}/chunks`);
			setChunks(data.chunks || []);
		} catch {
			toast.error('加载分片失败');
		} finally {
			setChunksLoading(false);
		}
	};

	useEffect(() => {
		fetchKbs();
	}, []);

	useEffect(() => {
		if (selectedKb) fetchDocs(selectedKb.id);
	}, [selectedKb]);

	const handleCreate = async () => {
		if (!newName.trim()) return;
		try {
			await client.post('/api/knowledge/', { name: newName, description: newDesc });
			toast.success('知识库创建成功');
			setShowCreate(false);
			setNewName('');
			setNewDesc('');
			fetchKbs();
		} catch {
			toast.error('创建失败');
		}
	};

	const handleDelete = async (id: number) => {
		if (!confirm('确定删除此知识库？所有文档将被清除。')) return;
		try {
			await client.delete(`/api/knowledge/${id}`);
			toast.success('已删除');
			if (selectedKb?.id === id) setSelectedKb(null);
			fetchKbs();
		} catch {
			toast.error('删除失败');
		}
	};

	const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
		if (!selectedKb || !e.target.files?.[0]) return;
		const file = e.target.files[0];
		const form = new FormData();
		form.append('file', file);
		form.append('knowledge_base_id', String(selectedKb.id));

		// Step 0: 上传
		setPipelineStep(0);
		setProcessingDocId(-1); // 临时 ID

		try {
			const { getUserId } = await import('@/api/client');
			const uploadRes = await fetch('/api/document/upload', {
				method: 'POST',
				headers: { 'X-User-ID': getUserId() },
				body: form,
			});
			if (!uploadRes.ok) {
				const err = await uploadRes.json();
				toast.error(err.detail || '上传失败');
				setPipelineStep(-1);
				setProcessingDocId(null);
				return;
			}
			const doc = await uploadRes.json();
			setProcessingDocId(doc.id);

			// Step 1-4: 处理（后端会依次完成解析、分片、向量化、索引）
			setPipelineStep(1);
			const result = await client.post<{ filename: string; chunk_count: number }>(`/api/document/${doc.id}/process`);
			setPipelineStep(4);
			toast.success(`处理完成: ${result.filename} (${result.chunk_count} 个分片)`);

			// 刷新列表
			setTimeout(() => {
				fetchDocs(selectedKb.id);
				fetchKbs();
				setPipelineStep(-1);
				setProcessingDocId(null);
			}, 1000);
		} catch {
			toast.error('上传失败');
			setPipelineStep(-1);
			setProcessingDocId(null);
		}
		e.target.value = '';
	};

	const handleDeleteDoc = async (docId: number) => {
		if (!confirm('确定删除此文档？')) return;
		try {
			await client.delete(`/api/document/${docId}`);
			toast.success('已删除');
			if (selectedKb) {
				fetchDocs(selectedKb.id);
				fetchKbs();
			}
		} catch {
			toast.error('删除失败');
		}
	};

	const formatSize = (bytes: number) => {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
	};

	const statusLabel = (doc: Document) => {
		switch (doc.status) {
			case 'completed': return { text: '已完成', cls: 'text-green-600' };
			case 'processing': return { text: '处理中', cls: 'text-yellow-600' };
			case 'failed': return { text: '失败', cls: 'text-red-600' };
			case 'pending': return { text: '待处理', cls: 'text-muted-foreground' };
			default: return { text: doc.status, cls: 'text-muted-foreground' };
		}
	};

	return (
		<div className="flex h-full">
			{/* 左侧：知识库列表 */}
			<div className="w-72 border-r flex flex-col">
				<div className="p-4 border-b flex items-center justify-between">
					<h2 className="text-sm font-semibold">知识库</h2>
					<Button size="icon-sm" variant="ghost" onClick={() => setShowCreate(true)}>
						<Plus className="h-4 w-4" />
					</Button>
				</div>

				{showCreate && (
					<div className="p-3 border-b space-y-2">
						<Input
							placeholder="知识库名称"
							value={newName}
							onChange={(e) => setNewName(e.target.value)}
							className="h-8 text-sm"
						/>
						<Input
							placeholder="描述（可选）"
							value={newDesc}
							onChange={(e) => setNewDesc(e.target.value)}
							className="h-8 text-sm"
						/>
						<div className="flex gap-2">
							<Button size="sm" onClick={handleCreate}>创建</Button>
							<Button size="sm" variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
						</div>
					</div>
				)}

				<div className="flex-1 overflow-auto">
					{loading ? (
						<div className="p-4 text-sm text-muted-foreground">加载中...</div>
					) : kbs.length === 0 ? (
						<div className="p-4 text-sm text-muted-foreground">暂无知识库</div>
					) : (
						kbs.map((kb) => (
							<div
								key={kb.id}
								className={`flex items-center justify-between p-3 cursor-pointer hover:bg-accent ${
									selectedKb?.id === kb.id ? 'bg-accent' : ''
								}`}
								onClick={() => setSelectedKb(kb)}
							>
								<div className="flex items-center gap-2 min-w-0">
									<Database className="h-4 w-4 shrink-0 text-muted-foreground" />
									<div className="min-w-0">
										<div className="text-sm font-medium truncate">{kb.name}</div>
										<div className="text-xs text-muted-foreground">
											{kb.document_count} 文档 · {kb.chunk_count} 片段
										</div>
									</div>
								</div>
								<Button
									size="icon-xs"
									variant="ghost"
									onClick={(e) => {
										e.stopPropagation();
										handleDelete(kb.id);
									}}
								>
									<Trash2 className="h-3 w-3" />
								</Button>
							</div>
						))
					)}
				</div>
			</div>

			{/* 右侧：文档列表 */}
			<div className="flex-1 flex flex-col">
				{!selectedKb ? (
					<div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
						选择左侧知识库查看文档
					</div>
				) : (
					<>
						<div className="p-4 border-b flex items-center justify-between">
							<div>
								<h2 className="text-sm font-semibold">{selectedKb.name}</h2>
								{selectedKb.description && (
									<p className="text-xs text-muted-foreground mt-0.5">{selectedKb.description}</p>
								)}
							</div>
							<div className="flex gap-2">
								<label>
									<Button size="sm" asChild disabled={processingDocId !== null}>
										<span>
											<Plus className="h-3.5 w-3.5 mr-1" />
											上传文档
										</span>
									</Button>
									<input
										type="file"
										accept=".md,.pdf,.txt"
										className="hidden"
										onChange={handleUpload}
									/>
								</label>
								<Button
									size="sm"
									variant="outline"
									onClick={() => {
										fetchDocs(selectedKb.id);
										fetchKbs();
									}}
								>
									<RefreshCw className="h-3.5 w-3.5 mr-1" />
									刷新
								</Button>
							</div>
						</div>

						<div className="flex-1 overflow-auto">
							{/* Pipeline 进度 */}
							{pipelineStep >= 0 && (
								<div className="m-4 p-4 border rounded-lg bg-muted/30">
									<div className="flex items-center gap-2 mb-3">
										<Loader2 className="h-4 w-4 animate-spin text-primary" />
										<span className="text-sm font-medium">文档处理中...</span>
									</div>
									<div className="flex items-center gap-1">
										{PIPELINE_STEPS.map((step, i) => (
											<div key={step.key} className="flex items-center">
												<div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs ${
													i < pipelineStep ? 'bg-green-100 text-green-700' :
													i === pipelineStep ? 'bg-primary/10 text-primary font-medium' :
													'bg-muted text-muted-foreground'
												}`}>
													{i < pipelineStep ? '✓' : i === pipelineStep ? (
														<Loader2 className="h-3 w-3 animate-spin" />
													) : '○'}
													{step.label}
												</div>
												{i < PIPELINE_STEPS.length - 1 && (
													<div className={`w-6 h-px mx-0.5 ${i < pipelineStep ? 'bg-green-300' : 'bg-border'}`} />
												)}
											</div>
										))}
									</div>
								</div>
							)}

							{documents.length === 0 && pipelineStep < 0 ? (
								<div className="flex-1 flex items-center justify-center h-full text-muted-foreground text-sm py-20">
									暂无文档，点击上方按钮上传
								</div>
							) : (
								<div className="divide-y">
									{documents.map((doc) => {
										const st = statusLabel(doc);
										return (
											<div key={doc.id} className="flex items-center justify-between p-3 hover:bg-accent/50">
												<div className="flex items-center gap-3 min-w-0">
													<FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
													<div className="min-w-0">
														<div className="text-sm font-medium truncate">{doc.filename}</div>
														<div className="text-xs text-muted-foreground">
															{doc.file_type?.toUpperCase()} · {formatSize(doc.file_size)} · {doc.chunk_count} 片段
															<span className={`ml-2 ${st.cls}`}>{st.text}</span>
															{doc.status === 'failed' && doc.error_message && (
																<span className="ml-2 text-red-500 truncate max-w-[200px] inline-block align-bottom">
																	({doc.error_message})
																</span>
															)}
														</div>
													</div>
												</div>
												<div className="flex items-center gap-1">
													<Button
														size="icon-xs"
														variant="ghost"
														onClick={() => window.open(`/view/${doc.id}`, '_blank')}
														title="查看内容"
													>
														<Eye className="h-3 w-3" />
													</Button>
													<Button
														size="icon-xs"
														variant="ghost"
														onClick={() => fetchChunks(doc)}
														title="查看分片"
													>
														<ChevronRight className="h-3 w-3" />
													</Button>
													<Button
														size="icon-xs"
														variant="ghost"
														onClick={() => handleDeleteDoc(doc.id)}
													>
														<Trash2 className="h-3 w-3" />
													</Button>
												</div>
											</div>
										);
									})}
								</div>
							)}
						</div>
					</>
				)}
			</div>

			{/* 分片查看弹窗 */}
			<Dialog open={!!viewingDoc} onOpenChange={(open) => { if (!open) { setViewingDoc(null); setChunks([]); } }}>
				<DialogContent className="max-w-5xl w-[90vw] max-h-[85vh] flex flex-col overflow-hidden">
					<DialogHeader>
						<DialogTitle className="text-sm">
							{viewingDoc?.filename} — {chunks.length} 个分片
						</DialogTitle>
					</DialogHeader>
					<div className="flex-1 overflow-auto space-y-4 pr-2 min-h-0">
						{chunksLoading ? (
							<div className="text-center py-8 text-muted-foreground">加载中...</div>
						) : chunks.length === 0 ? (
							<div className="text-center py-8 text-muted-foreground">暂无分片</div>
						) : (
							chunks.map((chunk) => (
								<div key={chunk.id} className="border rounded-lg p-4 overflow-hidden">
									<div className="flex items-center gap-2 mb-2">
										<span className="text-xs font-mono bg-muted px-2 py-0.5 rounded shrink-0">
											#{chunk.chunk_index}
										</span>
										{chunk.section_title && (
											<span className="text-xs font-medium truncate">{chunk.section_title}</span>
										)}
										<span className="text-xs text-muted-foreground ml-auto shrink-0">
											{chunk.content.length} 字符
										</span>
									</div>
									<p className="text-sm whitespace-pre-wrap break-words text-foreground/80 overflow-hidden">
										{chunk.content}
									</p>
								</div>
							))
						)}
					</div>
				</DialogContent>
			</Dialog>
		</div>
	);
}
