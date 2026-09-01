import type {
  PlatformDraft,
  PlatformSkillMetadata,
  PlatformStyle,
  PlatformStyleAdaptation,
} from '@/types'

type AnyRecord = Record<string, any>

export interface NormalizedPlatformResult {
  target_style?: string
  draft: PlatformDraft
  style_adaptation: PlatformStyleAdaptation
  generation_metadata: PlatformSkillMetadata
}

export const PLATFORM_EDITABLE_CONTENT_SOURCE = 'merchant_form'

const PLATFORM_KEYS: PlatformStyle[] = [
  'pinduoduo',
  'taobao',
  'jd',
  'suning',
  'xiaohongshu',
]

function asRecord(value: unknown): AnyRecord {
  if (typeof value === 'string') {
    try {
      return asRecord(JSON.parse(value))
    } catch {
      return {}
    }
  }
  return value && typeof value === 'object' && !Array.isArray(value)
    ? { ...(value as AnyRecord) }
    : {}
}

/** Mark the form snapshot so reload can restore merchant edits over generated copy. */
export function markEditablePlatformContent(value: unknown): Record<string, unknown> {
  return {
    ...asRecord(value),
    user_edited: true,
    source: PLATFORM_EDITABLE_CONTENT_SOURCE,
  }
}

export function isEditablePlatformContent(value: unknown): boolean {
  const record = asRecord(value)
  return record.user_edited === true || record.source === PLATFORM_EDITABLE_CONTENT_SOURCE
}

function hasValue(value: unknown): boolean {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function firstValue(...values: unknown[]): unknown {
  return values.find(hasValue)
}

function ownValue(record: AnyRecord, keys: string[]): { present: boolean; value: unknown } {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(record, key)) {
      return { present: true, value: record[key] }
    }
  }
  return { present: false, value: undefined }
}

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : hasValue(value) ? String(value).trim() : ''
}

function textList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      // Arrays are already itemized by the current schema. Preserve commas,
      // semicolons, and other punctuation inside each item; only a legacy
      // scalar string below is split into list items.
      .flatMap(item => {
        if (Array.isArray(item)) return textList(item)
        if (item && typeof item === 'object') {
          const record = item as AnyRecord
          const raw = firstValue(
            record.text,
            record.value,
            record.name,
            record.selling_point,
            record.adapted_selling_point,
          )
          return hasValue(raw) ? [text(raw)] : []
        }
        const itemText = text(item)
        return itemText ? [itemText] : []
      })
      .filter(Boolean)
  }
  if (value && typeof value === 'object') {
    const item = value as AnyRecord
    return textList(firstValue(
      item.text,
      item.value,
      item.name,
      item.selling_point,
      item.adapted_selling_point,
    ))
  }
  if (typeof value !== 'string') return []
  return value
    .split(/[\n,，、；;]+/)
    .map(item => item.trim())
    .filter(Boolean)
}

function normalizeTitleList(...values: unknown[]): string[] {
  for (const value of values) {
    const titles = Array.isArray(value)
      ? value.map(item => text(item)).filter(Boolean)
      : [text(value)].filter(Boolean)
    if (titles.length > 0) return titles.slice(0, 1)
  }
  return []
}

function platformMap(value: unknown): AnyRecord {
  const record = asRecord(value)
  const nested = asRecord(record.previews || record.platform_previews)
  if (Object.keys(nested).length > 0) return nested
  if (PLATFORM_KEYS.some(key => record[key] && typeof record[key] === 'object')) return record
  return {}
}

function resolveTargetStyle(root: AnyRecord, adaptation: AnyRecord, fallback?: string): string | undefined {
  const generation = asRecord(root.generation_metadata)
  const skill = asRecord(firstValue(
    adaptation.platform_skill,
    generation.platform_skill,
    root.platform_skill,
  ))
  const value = firstValue(
    adaptation.target_style,
    adaptation.targetStyle,
    root.target_style,
    root.targetStyle,
    root.platform_style,
    root.platformStyle,
    generation.target_style,
    generation.targetStyle,
    skill.target_style,
    skill.targetStyle,
    fallback,
  )
  return hasValue(value) ? String(value) : undefined
}

/**
 * Extract the platform Skill provenance without inventing a version for old
 * drafts. The returned nulls are intentional: they distinguish “not recorded”
 * from a fabricated/default Skill version.
 */
export function extractPlatformSkillMetadata(
  source: unknown,
  fallbackTargetStyle?: string,
): PlatformSkillMetadata {
  const root = asRecord(source)
  const nestedAdaptation = asRecord(root.style_adaptation)
  const adaptation = Object.keys(nestedAdaptation).length > 0 ? nestedAdaptation : root
  const generation = asRecord(root.generation_metadata)
  const skill = asRecord(firstValue(
    adaptation.platform_skill,
    generation.platform_skill,
    root.platform_skill,
  ))
  const targetStyle = resolveTargetStyle(root, adaptation, fallbackTargetStyle)
  const skillId = firstValue(
    adaptation.platform_skill_id,
    adaptation.platformSkillId,
    generation.platform_skill_id,
    generation.platformSkillId,
    root.platform_skill_id,
    root.platformSkillId,
    skill.id,
    skill.platform_skill_id,
  )
  const skillVersion = firstValue(
    adaptation.platform_skill_version,
    adaptation.platformSkillVersion,
    generation.platform_skill_version,
    generation.platformSkillVersion,
    root.platform_skill_version,
    root.platformSkillVersion,
    skill.version,
    skill.platform_skill_version,
  )
  const fallback = firstValue(
    adaptation.fallback,
    generation.fallback,
    root.fallback,
    skill.fallback,
  )

  return {
    ...(targetStyle ? { target_style: targetStyle } : {}),
    platform_skill_id: hasValue(skillId) ? String(skillId) : null,
    platform_skill_version: hasValue(skillVersion) ? String(skillVersion) : null,
    fallback: fallback === true,
  }
}

/** Normalize both current and legacy copy payloads into one stable draft. */
export function normalizePlatformDraft(source: unknown, fallbackSource?: unknown): PlatformDraft {
  const primary = asRecord(source)
  const fallback = asRecord(fallbackSource)
  const nestedDraft = asRecord(firstValue(primary.draft, primary.copy, fallback.draft, fallback.copy))
  const field = (...keys: string[]): unknown => {
    for (const record of [nestedDraft, primary, fallback]) {
      const result = ownValue(record, keys)
      // An explicitly empty field in the authoritative draft is meaningful;
      // do not silently replace it with a value from an older envelope.
      if (result.present && result.value !== undefined) return result.value
    }
    return undefined
  }
  const titleValue = field('titles', 'title')
  const sellingPointsValue = field('selling_points', 'sellingPoints', 'adapted_selling_points')
  const detailValue = field('detail_copy', 'detailCopy', 'detail', 'adapted_detail')
  const titleFallback = [primary.adapted_title, primary.title, primary.titles, fallback.adapted_title, fallback.title, fallback.titles]
  const sellingPointsFallback = [primary.adapted_selling_points, primary.selling_points, primary.sellingPoints, fallback.adapted_selling_points, fallback.selling_points, fallback.sellingPoints]
  const detailFallback = [primary.adapted_detail, primary.detail_copy, primary.detail, fallback.adapted_detail, fallback.detail_copy, fallback.detail]
  const draft: PlatformDraft = {
    titles: titleValue !== undefined ? normalizeTitleList(titleValue) : normalizeTitleList(...titleFallback),
    selling_points: sellingPointsValue !== undefined ? textList(sellingPointsValue) : textList(sellingPointsFallback.find(value => textList(value).length > 0)),
    detail_copy: detailValue !== undefined ? text(detailValue) : text(firstValue(...detailFallback)),
    subtitle: text(field('subtitle')),
    price_suggestion: (() => {
      const value = field('price_suggestion', 'priceSuggestion')
      if (!hasValue(value)) return null
      const number = Number(value)
      return Number.isFinite(number) ? number : null
    })(),
    specifications: textList(field('specifications')),
    target_audience: text(field('target_audience', 'targetAudience')),
    usage_scenarios: textList(field('usage_scenarios', 'usageScenarios')),
    seo_keywords: textList(field('seo_keywords', 'seoKeywords')),
    promotion_copy: text(field('promotion_copy', 'promotionCopy')),
    short_video_script: text(field('short_video_script', 'shortVideoScript', 'video')),
    pending_confirmations: textList(field('pending_confirmations', 'pendingConfirmations')),
  }
  return draft
}

/**
 * Keep exactly one target platform in a style result. This is also the legacy
 * compatibility boundary: old five-platform maps are filtered here before
 * they reach the editor or persistence payload.
 */
export function filterSinglePlatformResult(
  source: unknown,
  targetStyle?: string,
): NormalizedPlatformResult {
  const root = asRecord(source)
  const nestedAdaptation = asRecord(root.style_adaptation)
  const adaptation = Object.keys(nestedAdaptation).length > 0 ? nestedAdaptation : root
  const resolvedTarget = resolveTargetStyle(root, adaptation, targetStyle)
  const map = platformMap(adaptation)
  const selected = resolvedTarget && map[resolvedTarget] && typeof map[resolvedTarget] === 'object'
    ? asRecord(map[resolvedTarget])
    : {}
  const hasDirectCopy = [
    adaptation.draft,
    adaptation.adapted_title,
    adaptation.adapted_selling_points,
    adaptation.adapted_detail,
    adaptation.detail_copy,
    adaptation.selling_points,
    adaptation.titles,
  ].some(value => value !== undefined)
  const sourceForDraft = Object.keys(selected).length > 0
    ? { ...adaptation, ...selected }
    : (hasDirectCopy ? adaptation : (root.copy || root.draft || root.extended_content || adaptation))
  const draft = normalizePlatformDraft(
    sourceForDraft,
    root.copy || root.draft || root.extended_content,
  )
  if (
    !Object.prototype.hasOwnProperty.call(sourceForDraft as AnyRecord, 'pending_confirmations')
    && !Object.prototype.hasOwnProperty.call(asRecord((sourceForDraft as AnyRecord).draft), 'pending_confirmations')
    && root.pending_confirmations !== undefined
  ) {
    draft.pending_confirmations = textList(root.pending_confirmations)
  }
  const authoritativeDraft = Boolean(
    (sourceForDraft as AnyRecord).draft
    || (sourceForDraft as AnyRecord).copy,
  )
  const metadata = extractPlatformSkillMetadata(
    { ...root, style_adaptation: { ...adaptation, ...selected } },
    resolvedTarget,
  )

  const normalizedAdaptation: AnyRecord = {
    ...adaptation,
    ...selected,
    ...(resolvedTarget ? { target_style: resolvedTarget } : {}),
    adapted_title: authoritativeDraft
      ? text(draft.titles[0])
      : text(firstValue(
        selected.adapted_title,
        adaptation.adapted_title,
        draft.titles[0],
      )),
    adapted_selling_points: draft.selling_points,
    adapted_detail: authoritativeDraft
      ? text(draft.detail_copy)
      : text(firstValue(
        selected.adapted_detail,
        adaptation.adapted_detail,
        draft.detail_copy,
      )),
    draft,
    platform_skill_id: metadata.platform_skill_id,
    platform_skill_version: metadata.platform_skill_version,
    pending_confirmations: draft.pending_confirmations || [],
    fallback: metadata.fallback,
  }
  delete normalizedAdaptation.platform_previews
  delete normalizedAdaptation.previews
  for (const key of PLATFORM_KEYS) delete normalizedAdaptation[key]
  if (resolvedTarget) {
    normalizedAdaptation.previews = {
      [resolvedTarget]: {
        ...normalizedAdaptation,
        previews: undefined,
        platform_previews: undefined,
      },
    }
    delete normalizedAdaptation.previews[resolvedTarget].previews
    delete normalizedAdaptation.previews[resolvedTarget].platform_previews
  }

  return {
    ...(resolvedTarget ? { target_style: resolvedTarget } : {}),
    draft,
    style_adaptation: normalizedAdaptation as PlatformStyleAdaptation,
    generation_metadata: metadata,
  }
}

/** Build the persisted aiStylePreviews envelope while retaining old fields. */
export function buildPlatformDraftPayload(
  source: unknown,
  generationMetadata?: unknown,
  extendedContent?: unknown,
  targetStyle?: string,
): Record<string, unknown> {
  const normalized = filterSinglePlatformResult(source, targetStyle)
  const rawGenerationMetadata = generationMetadata === undefined
    ? asRecord(asRecord(source).generation_metadata)
    : asRecord(generationMetadata)
  const metadata = {
    ...rawGenerationMetadata,
    ...extractPlatformSkillMetadata(
      generationMetadata === undefined
        ? source
        : { ...(asRecord(source)), generation_metadata: generationMetadata },
      normalized.target_style,
    ),
  }
  const extension = asRecord(extendedContent)
  // The normalized Skill draft is authoritative. Form fields remain in the
  // compatibility envelope, but must not refill explicitly empty draft
  // fields (subtitle/promotion/video in particular).
  const draft: PlatformDraft = normalized.draft
  const adaptation = {
    ...normalized.style_adaptation,
    draft,
    platform_skill_id: metadata.platform_skill_id,
    platform_skill_version: metadata.platform_skill_version,
    fallback: metadata.fallback,
  }
  return {
    style_adaptation: adaptation,
    draft,
    generation_metadata: metadata,
    extended_content: extension,
  }
}

/** Merge provenance into aiDraftMeta without dropping image/input metadata. */
export function mergePlatformDraftMeta(
  existing: unknown,
  source: unknown,
  targetStyle?: string,
): Record<string, unknown> {
  const current = asRecord(existing)
  const metadata = extractPlatformSkillMetadata(source, targetStyle)
  const previousTarget = text(firstValue(
    current.platform_style,
    current.target_style,
    asRecord(current.platform_skill).target_style,
  ))
  const changedTarget = Boolean(metadata.target_style && previousTarget && metadata.target_style !== previousTarget)
  const merged: Record<string, unknown> = { ...current }
  if (metadata.target_style) {
    merged.platform_style = metadata.target_style
    merged.target_style = metadata.target_style
  }
  if (metadata.platform_skill_id !== null || metadata.fallback || changedTarget || current.platform_skill_id === undefined) {
    merged.platform_skill_id = metadata.platform_skill_id
  }
  if (metadata.platform_skill_version !== null || metadata.fallback || changedTarget || current.platform_skill_version === undefined) {
    merged.platform_skill_version = metadata.platform_skill_version
  }
  if (metadata.target_style || metadata.platform_skill_id !== null || metadata.platform_skill_version !== null || metadata.fallback) {
    merged.platform_skill = {
      ...(asRecord(current.platform_skill)),
      ...(metadata.target_style ? { target_style: metadata.target_style } : {}),
      id: metadata.platform_skill_id,
      version: metadata.platform_skill_version,
      fallback: metadata.fallback,
    }
    merged.platform_skill_fallback = metadata.fallback
  }
  return merged
}

export const normalizePlatformResult = filterSinglePlatformResult
