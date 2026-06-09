import type {
	ContentBlock,
	DataBlock,
	Msg,
	TextBlock,
	ToolCallBlock,
} from '@agentscope-ai/agentscope/message';
import {
	ArrowDown,
	ArrowUp,
	Bot,
	CalendarClock,
	CheckCircle,
	ChevronDownIcon,
	Copy,
	FileText,
	Loader2,
	MessageSquareQuote,
	Wrench,
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { ConfirmCard } from './ConfirmCard';
import { renderToolGroup } from './tool-renderers';
import type { TFunction, ToolCallWithResult } from './tool-renderers/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from '@/components/ui/collapsible.tsx';
import { Item, ItemContent } from '@/components/ui/item.tsx';
import { useTranslation } from '@/i18n/useI18n';
import { formatNumber, formatTime } from '@/utils/common';

interface ToolCallGroupBlock {
	type: 'tool_call_group';
	id: string;
	toolName: string;
	calls: ToolCallWithResult[];
}

type ExtendedContentBlock = ContentBlock | ToolCallGroupBlock;

/**
 * Group tool_call blocks of the same name into a single
 * `tool_call_group`, with each call paired to its matching
 * tool_result by id.
 *
 * Unlike the previous implementation this does NOT require calls of
 * the same name to be consecutive. When the agent issues multiple
 * concurrent tool calls (e.g. Glob + Grep), the content layout is
 * `[call_Glob, call_Grep, result_Glob, result_Grep]` — the old
 * "consecutive-same-name" approach would split call and result into
 * separate groups. This version collects all calls first (preserving
 * encounter order), then matches results, and finally emits groups
 * in the order the first call of each tool name appeared,
 * interleaved with non-tool blocks at their original positions.
 */
function groupToolCalls(content: ContentBlock[]): ExtendedContentBlock[] {
	// Pass 1: pair calls ↔ results by id, track non-tool blocks.
	const callMap = new Map<string, ToolCallWithResult>();
	const resultMap = new Map<string, ContentBlock>();
	const ordering: Array<{ type: 'tool'; id: string } | { type: 'other'; block: ContentBlock }> =
		[];

	for (const block of content) {
		if (block.type === 'tool_call') {
			const entry: ToolCallWithResult = { call: block };
			callMap.set(block.id, entry);
			ordering.push({ type: 'tool', id: block.id });
		} else if (block.type === 'tool_result') {
			const matching = callMap.get(block.id);
			if (matching) {
				matching.result = block;
			} else {
				resultMap.set(block.id, block);
			}
		} else {
			ordering.push({ type: 'other', block });
		}
	}

	// Pass 2: walk the ordering, group consecutive same-name calls
	// (now that results are already attached).
	const result: ExtendedContentBlock[] = [];
	let currentGroup: ToolCallWithResult[] = [];
	let currentToolName: string | null = null;

	const flush = () => {
		if (currentGroup.length > 0 && currentToolName) {
			result.push({
				type: 'tool_call_group',
				id: crypto.randomUUID(),
				toolName: currentToolName,
				calls: currentGroup,
			});
			currentGroup = [];
			currentToolName = null;
		}
	};

	for (const item of ordering) {
		if (item.type === 'other') {
			flush();
			result.push(item.block);
		} else {
			const entry = callMap.get(item.id);
			if (!entry) continue;
			if (currentToolName !== null && currentToolName !== entry.call.name) {
				flush();
			}
			currentToolName = entry.call.name;
			currentGroup.push(entry);
		}
	}
	flush();

	// Orphan results (no matching call) — render as synthetic groups.
	for (const [id, block] of resultMap) {
		if (block.type === 'tool_result') {
			result.push({
				type: 'tool_call_group',
				id: crypto.randomUUID(),
				toolName: block.name,
				calls: [
					{
						call: {
							type: 'tool_call',
							id,
							name: block.name,
							input: '',
							state: 'finished' as const,
						},
						result: block,
					},
				],
			});
		}
	}

	return result;
}

/**
 * Render a single content block. Tool call groups are dispatched to
 * `renderToolGroup`; the per-group truncation at the first `asking` call
 * (and the trailing ConfirmCard) lives here so renderers only see a clean
 * list of calls.
 */
function renderBlock(
	block: ExtendedContentBlock,
	index: number,
	t: TFunction,
	onUserConfirm?: (
		toolCallBlock: ToolCallBlock,
		confirm: boolean,
		rules?: ToolCallBlock['suggested_rules'],
	) => void,
	message?: Msg,
) {
	switch (block.type) {
		case 'tool_call_group': {
			const firstAsk = block.calls.findIndex((item) => item.call.state === 'asking');
			const visible = firstAsk === -1 ? block.calls : block.calls.slice(0, firstAsk + 1);
			const askingCall = firstAsk === -1 ? null : block.calls[firstAsk].call;
			return (
				<div key={index} className="flex flex-col gap-y-4 text-muted-foreground">
					{renderToolGroup(block.toolName, visible, t)}
					{askingCall && (
						<ConfirmCard
							toolCall={askingCall}
							onUserConfirm={(confirm, rules) => {
								if (onUserConfirm) onUserConfirm(askingCall, confirm, rules);
							}}
						/>
					)}
				</div>
			);
		}
		case 'text': {
			// 解析引用数据（从同一个 message 的 hint block 中获取）
			const refHint = message?.content?.find(
				(b: any) => b.type === 'hint' && b.source === 'milo-retrieval',
			) as any;
			let refMap: Record<string, string> = {};
			if (refHint && typeof refHint.hint === 'string') {
				try {
					const parsed = JSON.parse(refHint.hint);
					for (const ref of parsed.references || []) {
						refMap[String(ref.index)] = ref.doc_id;
					}
				} catch { /* ignore */ }
			}

			// 递归处理 children，将 [n] 转为链接
			const processChildren = (children: React.ReactNode): React.ReactNode => {
				if (typeof children === 'string') {
					const parts = children.split(/(\[\d+\])/g);
					if (parts.length === 1) return children;
					return parts.map((part, i) => {
						const match = part.match(/^\[(\d+)\]$/);
						if (match && refMap[match[1]]) {
							return (
								<a
									key={i}
									href={`/view/${refMap[match[1]]}`}
									target="_blank"
									rel="noopener noreferrer"
									className="text-primary underline underline-offset-2 hover:text-primary/80"
								>
									{part}
								</a>
							);
						}
						return part;
					});
				}
				if (Array.isArray(children)) {
					return children.map((child, i) => (
						<React.Fragment key={i}>{processChildren(child)}</React.Fragment>
					));
				}
				return children;
			};

			return (
				<div key={index} className="prose prose-sm w-full min-w-full">
					<ReactMarkdown
						remarkPlugins={[remarkGfm]}
						components={{
							p: ({ children }) => <p>{processChildren(children)}</p>,
							li: ({ children }) => <li>{processChildren(children)}</li>,
							code: ({ className, children, ...props }) => {
								const isInline = !String(className ?? '').startsWith('language-');
								if (isInline) {
									return (
										<code className={`${className ?? ''} break-all`} {...props}>
											{children}
										</code>
									);
								}
								return (
									<div className="relative w-full">
										<Button
											size="icon-xs"
											variant="ghost"
											className="absolute top-0 right-0 z-10"
											onClick={async (e) => {
												e.preventDefault();
												e.stopPropagation();
												await navigator.clipboard.writeText(
													String(children),
												);
											}}
										>
											<Copy />
										</Button>
										<div className="overflow-x-auto max-w-full w-full">
											<code className={className} {...props}>
												{children}
											</code>
										</div>
									</div>
								);
							},
						}}
					>
						{block.text}
					</ReactMarkdown>
				</div>
			);
		}

		case 'thinking':
			return (
				<details key={index} className="group mb-3" open>
					<summary className="cursor-pointer select-none text-sm text-muted-foreground flex items-center gap-1.5 hover:text-foreground transition-colors">
						<svg className="h-3.5 w-3.5 shrink-0 transition-transform group-open:rotate-90" viewBox="0 0 16 16" fill="currentColor">
							<path d="M6 3l5 5-5 5V3z" />
						</svg>
						{t('messageBubble.thinking')}
					</summary>
					<p className="mt-2 ml-5 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{block.thinking}</p>
				</details>
			);

		case 'data': {
			const dataType = block.source.media_type.split('/')[0];
			let data: string;
			if (block.source.type === 'url') {
				data = block.source.url;
			} else {
				data = `data:${block.source.media_type};base64,${block.source.data}`;
			}
			switch (dataType) {
				case 'image':
					return <img key={index} src={data} alt="Uploaded image" />;
				case 'audio':
					return <audio key={index} controls src={data} />;
				case 'video':
					return <video key={index} controls src={data} />;
			}
			return null;
		}

		case 'hint': {
			// Milo retrieval references - render as a reference list with links
			if (block.source === 'milo-retrieval') {
				let refs: { index: number; name: string; doc_id: string }[] = [];
				try {
					const parsed = JSON.parse(block.hint as string);
					refs = parsed.references || [];
				} catch {
					// fallback: try to parse old format
				}
				return (
					<div key={index} className="rounded-lg border border-border/50 bg-muted/30 px-4 py-3 mb-3">
						<div className="text-xs font-medium text-muted-foreground mb-2">参考文档</div>
						<div className="flex flex-wrap gap-2">
							{refs.map((ref) => (
								<a
									key={ref.index}
									href={`/view/${ref.doc_id}`}
									target="_blank"
									rel="noopener noreferrer"
									className="inline-flex items-center gap-1.5 rounded-md bg-background border px-2.5 py-1.5 text-xs hover:bg-accent transition-colors"
								>
									<FileText className="h-3 w-3 shrink-0 text-muted-foreground" />
									<span className="max-w-[200px] truncate">{ref.name}</span>
								</a>
							))}
						</div>
					</div>
				);
			}

			// Parse source: try JSON, fall back to plain string, default to t('common.message').
			let hintLabel: string;
			let hintSublabel: string | null = null;
			let HintIcon = MessageSquareQuote;

			if (block.source) {
				try {
					const parsed = JSON.parse(block.source) as {
						label?: string;
						sublabel?: string;
					};
					hintLabel = parsed.label
						? t(`messageBubble.hintSource.${parsed.label}`)
						: block.source;
					hintSublabel = parsed.sublabel ?? null;
					if (parsed.label === 'team_message') HintIcon = Bot;
					else if (parsed.label === 'schedule') HintIcon = CalendarClock;
					else if (parsed.label === 'tool_output') HintIcon = Wrench;
				} catch {
					hintLabel = block.source;
				}
			} else {
				hintLabel = t('common.message');
			}
			const items: (TextBlock | DataBlock)[] =
				typeof block.hint === 'string'
					? [{ type: 'text', id: `${block.id}-text`, text: block.hint }]
					: block.hint;
			return (
				<Item variant={'outline'} className="max-w-full">
					<ItemContent className="max-w-full">
						<Collapsible>
							<CollapsibleTrigger asChild>
								<Button className="group w-full max-w-full" variant="ghost">
									<HintIcon className="size-3.5" />
									<span className="tracking-tight">{hintLabel}</span>
									{hintSublabel && (
										<span className="text-muted-foreground font-normal truncate max-w-[200px]">
											{hintSublabel}
										</span>
									)}
									<ChevronDownIcon className="ml-auto group-data-[state=open]:rotate-180" />
								</Button>
							</CollapsibleTrigger>
							<CollapsibleContent className="p-2.5 pt-0 max-w-full overflow-hidden break-all text-muted-foreground">
								{items.map((inner, i) => renderBlock(inner, i, t))}
							</CollapsibleContent>
						</Collapsible>
					</ItemContent>
				</Item>
			);
		}

		default:
			return null;
	}
}

interface MessageBubbleProps {
	message: Msg;
	onUserConfirm: (
		toolCallBlock: ToolCallBlock,
		confirm: boolean,
		replyId: string,
		rules?: ToolCallBlock['suggested_rules'],
	) => void;
}

/**
 * A message bubble component that displays a chat message.
 *
 * Running state is derived from `message.finished_at`: a missing or null
 * `finished_at` means the agent is still producing this reply. The bottom
 * status row shows a single left-aligned badge laid out as
 * `[state-icon] [duration] [↑in ↓out]`:
 *   - State icon: spinning `Loader2` while running, static `CheckCircle`
 *     once finished.
 *   - Duration is `now - created_at` while running (ticking each second),
 *     `finished_at - created_at` once complete.
 *   - Token counts only appear once `usage` is populated with non-zero
 *     values — typically after the message finishes.
 *
 * When `content` is empty and the message is still running, the bubble
 * body is omitted entirely so only the bottom status row renders.
 */
export function MessageBubble({ message, onUserConfirm }: MessageBubbleProps) {
	const isUser = message.role === 'user';
	const { t } = useTranslation();

	const isRunning = !message.finished_at;
	const hasUsage =
		!!message.usage &&
		((message.usage.input_tokens ?? 0) > 0 || (message.usage.output_tokens ?? 0) > 0);

	// Tick once per second while running so the elapsed time updates live.
	const [now, setNow] = useState(() => Date.now());
	useEffect(() => {
		if (!isRunning) return;
		const id = setInterval(() => setNow(Date.now()), 1000);
		return () => clearInterval(id);
	}, [isRunning]);

	const blocks = groupToolCalls(message.content);
	const showBody = blocks.length > 0;
	const showFooter = !isUser;

	const startMs = new Date(message.created_at).getTime();
	const endMs = isRunning ? now : new Date(message.finished_at!).getTime();
	const elapsedSeconds = Math.max(0, (endMs - startMs) / 1000);
	const elapsedText = formatTime(elapsedSeconds);

	return (
		<div
			className={`flex flex-col w-full max-w-full ${isUser ? 'items-end' : 'items-start'} mb-4`}
		>
			{showBody && (
				<div
					className={`p-4 rounded-xl space-y-3 max-w-full ${
						isUser ? 'w-fit bg-secondary' : 'w-full min-w-full'
					}`}
				>
					{blocks.map((block, i) =>
						renderBlock(
							block,
							i,
							t,
							(
								toolCall: ToolCallBlock,
								confirm: boolean,
								rules?: ToolCallBlock['suggested_rules'],
							) => {
								onUserConfirm(toolCall, confirm, message.id, rules);
								toolCall.state = confirm ? 'allowed' : 'finished';
							},
							message,
						),
					)}
				</div>
			)}
			{showFooter && (
				<div className="flex flex-row items-center text-muted-foreground gap-x-4 px-2 w-full">
					<Badge
						variant="secondary"
						aria-label={isRunning ? t('messageBubble.running') : undefined}
					>
						{isRunning ? (
							<Loader2 data-icon="inline-start" className="animate-spin" />
						) : (
							<CheckCircle data-icon="inline-start" />
						)}
						<span className="tabular-nums tracking-tighter">{elapsedText}</span>
						{hasUsage && (
							<>
								<ArrowUp data-icon="inline-start" className="ml-1" />
								<span className="tabular-nums">
									{formatNumber(message.usage?.input_tokens ?? 0)}
								</span>
								<ArrowDown data-icon="inline-start" className="ml-1" />
								<span className="tabular-nums">
									{formatNumber(message.usage?.output_tokens ?? 0)}
								</span>
							</>
						)}
					</Badge>
				</div>
			)}
		</div>
	);
}
