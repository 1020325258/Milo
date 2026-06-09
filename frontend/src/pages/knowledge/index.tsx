import { useEffect, useState } from 'react';
import { Database, Plus, Trash2, FileText, RefreshCw, Eye, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

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
	created_at: string;
}

interface Chunk {
	id: number;
	chunk_id: string;
	chunk_index: number;
	content: string;
	section_title: string | null;
}

const API_BASE = '/api';

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

	const fetchKbs = async () => {
		setLoading(true);
		try {
			const res = await fetch(`${API_BASE}/knowledge/?page=1&page_size=100`);
			const data = await res.json();
			setKbs(data.items || []);
		} catch {
			toast.error('加载知识库失败');
		} finally {
			setLoading(false);
		}
	};

	const fetchDocs = async (kbId: number) => {
		try {
			const res = await fetch(`${API_BASE}/document/?knowledge_base_id=${kbId}&page=1&page_size=100`);
			const data = await res.json();
			setDocuments(data.items || []);
		} catch {
			toast.error('加载文档失败');
		}
	};

	const fetchChunks = async (doc: Document) => {
		setChunksLoading(true);
		setViewingDoc(doc);
		try {
			const res = await fetch(`${API_BASE}/document/${doc.id}/chunks`);
			const data = await res.json();
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
			const res = await fetch(`${API_BASE}/knowledge/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: newName, description: newDesc }),
			});
			if (res.ok) {
				toast.success('知识库创建成功');
				setShowCreate(false);
				setNewName('');
				setNewDesc('');
				fetchKbs();
			} else {
				const err = await res.json();
				toast.error(err.detail || '创建失败');
			}
		} catch {
			toast.error('创建失败');
		}
	};

	const handleDelete = async (id: number) => {
		if (!confirm('确定删除此知识库？所有文档将被清除。')) return;
		try {
			const res = await fetch(`${API_BASE}/knowledge/${id}`, { method: 'DELETE' });
			if (res.ok) {
				toast.success('已删除');
				if (selectedKb?.id === id) setSelectedKb(null);
				fetchKbs();
			}
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
		try {
			const res = await fetch(`${API_BASE}/document/upload`, { method: 'POST', body: form });
			if (res.ok) {
				const doc = await res.json();
				toast.success(`上传成功: ${doc.filename}`);
				await fetch(`${API_BASE}/document/${doc.id}/process`, { method: 'POST' });
				toast.success('文档处理完成');
				fetchDocs(selectedKb.id);
				fetchKbs();
			} else {
				toast.error('上传失败');
			}
		} catch {
			toast.error('上传失败');
		}
		e.target.value = '';
	};

	const handleDeleteDoc = async (docId: number) => {
		if (!confirm('确定删除此文档？')) return;
		try {
			await fetch(`${API_BASE}/document/${docId}`, { method: 'DELETE' });
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
									<Button size="sm" asChild>
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
							{documents.length === 0 ? (
								<div className="flex-1 flex items-center justify-center h-full text-muted-foreground text-sm py-20">
									暂无文档，点击上方按钮上传
								</div>
							) : (
								<div className="divide-y">
									{documents.map((doc) => (
										<div key={doc.id} className="flex items-center justify-between p-3 hover:bg-accent/50">
											<div className="flex items-center gap-3 min-w-0">
												<FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
												<div className="min-w-0">
													<div className="text-sm font-medium truncate">{doc.filename}</div>
													<div className="text-xs text-muted-foreground">
														{doc.file_type?.toUpperCase()} · {formatSize(doc.file_size)} · {doc.chunk_count} 片段
														<span className={`ml-2 ${
															doc.status === 'completed' ? 'text-green-600' :
															doc.status === 'processing' ? 'text-yellow-600' :
															doc.status === 'failed' ? 'text-red-600' : 'text-muted-foreground'
														}`}>
															{doc.status === 'completed' ? '已完成' :
															 doc.status === 'processing' ? '处理中' :
															 doc.status === 'failed' ? '失败' : doc.status}
														</span>
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
									))}
								</div>
							)}
						</div>
					</>
				)}
			</div>

			{/* 分片查看弹窗 */}
			<Dialog open={!!viewingDoc} onOpenChange={(open) => { if (!open) { setViewingDoc(null); setChunks([]); } }}>
				<DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
					<DialogHeader>
						<DialogTitle className="text-sm">
							{viewingDoc?.filename} — {chunks.length} 个分片
						</DialogTitle>
					</DialogHeader>
					<div className="flex-1 overflow-auto space-y-4 pr-2">
						{chunksLoading ? (
							<div className="text-center py-8 text-muted-foreground">加载中...</div>
						) : chunks.length === 0 ? (
							<div className="text-center py-8 text-muted-foreground">暂无分片</div>
						) : (
							chunks.map((chunk) => (
								<div key={chunk.id} className="border rounded-lg p-4">
									<div className="flex items-center gap-2 mb-2">
										<span className="text-xs font-mono bg-muted px-2 py-0.5 rounded">
											#{chunk.chunk_index}
										</span>
										{chunk.section_title && (
											<span className="text-xs font-medium">{chunk.section_title}</span>
										)}
										<span className="text-xs text-muted-foreground ml-auto">
											{chunk.content.length} 字符
										</span>
									</div>
									<p className="text-sm whitespace-pre-wrap text-foreground/80">
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
