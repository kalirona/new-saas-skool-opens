/**
 * Script to migrate @phosphor-icons/react imports to lucide-react.
 * Reads PHOSPHOR_TO_LUCIDE mapping from lib/icon-mapping.ts
 * and transforms all affected files in the project.
 */

const fs = require('fs');
const path = require('path');

const WEB_ROOT = path.resolve(__dirname, '..');

// === Load PHOSPHOR_TO_LUCIDE mapping ===
function loadMapping() {
  const mappingPath = path.join(WEB_ROOT, 'lib', 'icon-mapping.ts');
  const content = fs.readFileSync(mappingPath, 'utf-8');
  // Extract the Record from the TS file
  const match = content.match(/export const PHOSPHOR_TO_LUCIDE: Record<string, string> = \{(.+?)\}/s);
  if (!match) throw new Error('Could not find PHOSPHOR_TO_LUCIDE mapping');
  const map = {};
  // Match all "Key: 'Value'" pairs
  const re = /(\w+):\s*'(\w+)'/g;
  let m;
  while ((m = re.exec(match[1])) !== null) {
    map[m[1]] = m[2];
  }
  return map;
}

// === Additional manual mappings from the task ===
const EXTRA_MAPPINGS = {
  MarkdownLogo: 'FileText',
  Browsers: 'Monitor',
  ChatsCircle: 'MessageCircle',
  FloppyDisk: 'Save',
  SpinnerGap: 'Loader',
  ClockCountdown: 'Timer',
  Chalkboard: 'Presentation',
  ChalkboardSimple: 'Presentation',
  Password: 'KeyRound',
  Selection: 'MousePointer2',
  ArrowsInLineVertical: 'Minimize2',
  CheckFat: 'CheckCheck',
  ArrowElbowRight: 'MoveRight',
  ArrowSquareOut: 'ExternalLink',
  ArrowClockwise: 'RotateCw',
  ArrowCounterClockwise: 'RotateCcw',
  SlidersHorizontal: 'SlidersHorizontal',
  CircleNotch: 'Loader',
  PaperPlaneTilt: 'Send',
  StarFour: 'Star',
  UserList: 'Users',
  Backpack: 'Backpack',
  Note: 'StickyNote',
  Article: 'FileText',
  Package: 'Package',
  EnvelopeSimple: 'Mail',
  PlusCircle: 'PlusCircle',
  TrendUp: 'TrendingUp',
  Funnel: 'Filter',
  Hourglass: 'Hourglass',
  ArrowsInSimple: 'Minimize',
  ArrowsLeftRight: 'ArrowLeftRight',
  Broadcast: 'Radio',
  Binoculars: 'Binoculars',
  UsersThree: 'Users',
  Buildings: 'Building2',
  ArrowLineLeft: 'ChevronFirst',
  ArrowLineRight: 'ChevronLast',
  Medal: 'Medal',
  Robot: 'Bot',
  Sparkle: 'Sparkle',
  Brain: 'Brain',
  SquareHalf: 'Columns2',
  CalendarBlank: 'Calendar',
  VideoCamera: 'Video',
  MapPin: 'MapPin',
  ArrowLineDown: 'ArrowDown',
  ArrowLineUp: 'ArrowUp',
  ArrowFatLineUp: 'ArrowUp',
  ArrowFatLineDown: 'ArrowDown',
  ArrowFatLineLeft: 'ArrowLeft',
  ArrowFatLineRight: 'ArrowRight',
  ArrowFatLinesUp: 'ArrowUp',
  ArrowFatLinesDown: 'ArrowDown',
  ArrowFatLinesLeft: 'ArrowLeft',
  ArrowFatLinesRight: 'ArrowRight',
  CaretDoubleLeft: 'ChevronsLeft',
  CaretDoubleRight: 'ChevronsRight',
  CaretCircleDown: 'ChevronDownCircle',
  CaretCircleUp: 'ChevronUpCircle',
};

// Direct matches (phosphor name is same as lucide name)
const DIRECT_MATCHES = [
  'Trash2', 'ExternalLink', 'Loader2', 'PlusCircle', 'Package', 'Hourglass',
  'Binoculars', 'Medal', 'Sparkle', 'Brain', 'MapPin', 'ArrowLeftRight',
  'SlidersHorizontal', 'Backpack', 'Calendar', 'ArrowLeft', 'ArrowRight',
  'ArrowDown', 'ArrowUp', 'X', 'Plus', 'Minus', 'Check', 'Circle', 'Square',
  'List', 'Menu', 'Info', 'Copy', 'Bell', 'Eye', 'Link', 'Code', 'Clock',
  'Star', 'Heart', 'Flag', 'Tag', 'Lock', 'Key', 'Moon', 'Sun', 'Cloud',
  'File', 'Folder', 'Book', 'Play', 'Pause', 'Stop', 'Shield', 'Trash',
  'Upload', 'Download', 'Search', 'Settings', 'User', 'Globe', 'Home',
  'Mail', 'Phone', 'Camera', 'Printer', 'Laptop', 'Wifi', 'Power',
  'Anchor', 'Bug', 'Leaf', 'Gift', 'Crown', 'Trophy', 'Award', 'Fire',
  'Rocket', 'Wrench', 'Hammer', 'Nut', 'Plug', 'Wallet', 'CreditCard',
  'Music', 'Video', 'Table', 'Terminal', 'Palette', 'Ruler', 'Hand',
  'Compass', 'Crosshair', 'Gauge', 'Bluetooth', 'Cast', 'Bus', 'Car',
  'Bike', 'Train', 'Ship', 'Truck', 'Coffee', 'Beer', 'Wine', 'Pizza',
  'Apple', 'Basket', 'ShoppingCart', 'ShoppingBag', 'Factory', 'Warehouse',
  'Hospital', 'Church', 'Mosque', 'Fence', 'Anchor', 'Telescope',
  'Magnet', 'GraduationCap', 'Podcast', 'Headphones', 'Microphone',
  'Thermometer', 'Droplet', 'Snowflake', 'Wind', 'Sunrise', 'Sunset',
  'ThumbsUp', 'ThumbsDown', 'ToggleLeft', 'ToggleRight', 'Lock',
  'Pen', 'Pencil', 'Image', 'Images', 'Paperclip', 'Link', 'Shuffle',
  'Repeat', 'Github', 'Twitter', 'Youtube', 'Facebook', 'Instagram',
  'Linkedin', 'Figma', 'Slack', 'Activity', 'Zap', 'Timer', 'Hourglass',
  'Calendar', 'CalendarCheck', 'CalendarPlus', 'CalendarX', 'CalendarDays',
  'UserPlus', 'UserMinus', 'UserCheck', 'UserX', 'UserCog', 'UserCircle',
  'BookOpen', 'Bookmark', 'BookmarkCheck', 'FolderPlus', 'FolderOpen',
  'FilePlus', 'FileCode', 'FileImage', 'FileText', 'FileX', 'FileDown',
  'FileUp', 'AlertTriangle', 'AlertCircle', 'AlertOctagon', 'HelpCircle',
  'CheckCircle', 'CheckSquare', 'XCircle', 'MinusCircle', 'PlusCircle',
  'ArrowUpCircle', 'ArrowDownCircle', 'ArrowLeftCircle', 'ArrowRightCircle',
  'FastForward', 'Rewind', 'Eject', 'SkipForward', 'SkipBack',
  'PlayCircle', 'PauseCircle', 'StopCircle', 'Volume1', 'Volume2',
  'VolumeX', 'BellOff', 'BellRing', 'EyeOff', 'ShieldCheck', 'ShieldAlert',
  'ShieldOff', 'Unlock', 'CheckCheck', 'Clipboard', 'ClipboardList',
  'NotepadText', 'StickyNote', 'StarHalf', 'HeartPulse', 'HeartOff',
  'MessageSquare', 'MessageCircle', 'MessagesSquare', 'AtSign', 'Hash',
  'Mailbox', 'PhoneCall', 'PhoneIncoming', 'PhoneOutgoing', 'PhoneOff',
  'CookingPot', 'Utensils', 'Hamburger', 'OrangeSlice', 'Landmark',
  'Barcode', 'QrCode', 'Recycle', 'TreePine', 'GitBranch', 'GitCommitHorizontal',
  'GitCompare', 'GitFork', 'GitMerge', 'GitPullRequest', 'BarChart3',
  'BarChartHorizontal', 'ChartLine', 'PieChart', 'TrendingUp', 'TrendingDown',
  'ScatterChart', 'Percent', 'Sigma', 'Pi', 'Calculator', 'DollarSign',
  'Euro', 'PoundSterling', 'Bitcoin', 'Divide', 'PlusMinus', 'Equals',
  'NotEqual', 'EqualApproximately', 'Infinity', 'Indent', 'Outdent',
  'Type', 'Text', 'TextCursor', 'TextCursorInput', 'Bold', 'Italic',
  'Strikethrough', 'Underline', 'Heading', 'Heading1', 'Heading2', 'Heading3',
  'Heading5', 'Heading6', 'ListOrdered', 'ListChecks', 'ListPlus',
  'ListMusic', 'Quote', 'AlignCenter', 'AlignLeft', 'AlignRight',
  'AlignJustify', 'Code2', 'Font', 'PaintBucket', 'Paintbrush',
  'SwatchBook', 'Wand2', 'Selection', 'MousePointer', 'MousePointerClick',
  'MousePointer2', 'Columns2', 'Columns3', 'Rows2', 'Rows3', 'LayoutGrid',
  'Grid3x3', 'GripVertical', 'MoreHorizontal', 'MoreVertical', 'Sliders',
  'LogIn', 'LogOut', 'ChevronDown', 'ChevronUp', 'ChevronLeft', 'ChevronRight',
  'ChevronDownCircle', 'ChevronUpCircle', 'ChevronsDown', 'ChevronsUp',
  'ChevronsLeft', 'ChevronsRight', 'ChevronFirst', 'ChevronLast',
  'Expand', 'Minimize', 'Minimize2', 'RotateCw', 'RotateCcw',
  'CornerDownLeft', 'CornerDownRight', 'CornerUpLeft', 'CornerUpRight',
  'MoveRight', 'MoveLeft', 'MoveUp', 'MoveDown', 'Send', 'Save',
  'Loader', 'Loader2', 'Filter', 'Radio', 'Building', 'Building2',
  'Store', 'Monitor', 'Smartphone', 'Tablet', 'MonitorPlay', 'MonitorUp',
  'Computer', 'Keyboard', 'Gamepad2', 'Scan', 'Stand', 'MousePointer2',
  'KeyRound', 'Presentaion', 'Presentation', 'Timer', 'ExternalLink',
  'Trash2', 'Bot', 'Square', 'CircleDot', 'CircleDashed',
];

const LUCIDE_ONLY = {};
for (const name of DIRECT_MATCHES) {
  LUCIDE_ONLY[name] = name;
}

// Combine all mappings
const PHOSPHOR_TO_LUCIDE = { ...loadMapping(), ...EXTRA_MAPPINGS };

// For any direct match, ensure it maps to itself
for (const [phosphor, lucide] of Object.entries(PHOSPHOR_TO_LUCIDE)) {
  // already loaded
}

/**
 * Parse a phosphor import line and return the list of imported specifiers.
 * Handles single and multi-line import statements.
 */
function parsePhosphorImports(content) {
  const results = [];
  // Match `import { ... } from '@phosphor-icons/react'`
  // This can span multiple lines
  const re = /import\s*\{([^}]+)\}\s*from\s*['"]@phosphor-icons\/react['"]/gs;
  let match;
  while ((match = re.exec(content)) !== null) {
    const block = match[1];
    // Parse individual specifiers (handles `Icon`, `Icon as Alias`, and comments)
    const specRe = /(\w+)(?:\s+as\s+(\w+))?/g;
    let specMatch;
    const specifiers = [];
    while ((specMatch = specRe.exec(block)) !== null) {
      const name = specMatch[1];
      const alias = specMatch[2] || null;
      specifiers.push({ name, alias, fullMatch: specMatch[0] });
    }
    results.push({
      fullMatch: match[0],
      startIndex: match.index,
      endIndex: match.index + match[0].length,
      specifiers,
    });
  }
  return results;
}

/**
 * Parse existing lucide-react imports to get already imported icons.
 */
function parseLucideImports(content) {
  const re = /import\s*\{([^}]+)\}\s*from\s*['"]lucide-react['"]/s;
  const match = re.exec(content);
  if (!match) return [];
  const block = match[1];
  const specRe = /(\w+)(?:\s+as\s+(\w+))?/g;
  const results = [];
  let m;
  while ((m = specRe.exec(block)) !== null) {
    results.push({ name: m[1], alias: m[2] || null });
  }
  return { fullMatch: match[0], icons: results, index: match.index, length: match[0].length };
}

/**
 * Escape special regex characters
 */
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Process a single file
 */
function processFile(filePath) {
  const original = fs.readFileSync(filePath, 'utf-8');
  let content = original;

  // Skip if no phosphor import
  if (!content.includes('@phosphor-icons/react')) return null;

  const phosphorImports = parsePhosphorImports(content);
  if (phosphorImports.length === 0) return null;

  // Collect all phosphor specifiers across all phosphor import statements
  const allPhosphorSpecifiers = [];
  for (const imp of phosphorImports) {
    for (const spec of imp.specifiers) {
      allPhosphorSpecifiers.push(spec);
    }
  }

  // Determine mapping for each specifier
  const mappedToLucide = []; // { lucideName, originalName, alias }
  const unmapped = []; // keep on phosphor

  for (const spec of allPhosphorSpecifiers) {
    let lucideName = PHOSPHOR_TO_LUCIDE[spec.name];
    if (!lucideName) {
      // Check if phosphor name IS a lucide name (direct match)
      if (LUCIDE_ONLY[spec.name]) {
        lucideName = spec.name;
      }
    }
    if (lucideName) {
      mappedToLucide.push({
        lucideName,
        originalName: spec.name,
        alias: spec.alias,
      });
    } else {
      unmapped.push(spec);
    }
  }

  // Get existing lucide import specifiers
  let existingLucide = parseLucideImports(content);
  const existingLucideNames = new Set((existingLucide.icons || []).map(i => i.name));

  // Build the new lucide icons list (merge existing + mapped, deduplicate by name)
  const finalLucideIcons = [];
  const seenLucideNames = new Set();

  // Start with existing lucide icons
  if (existingLucide.icons) {
    for (const icon of existingLucide.icons) {
      if (!seenLucideNames.has(icon.name)) {
        seenLucideNames.add(icon.name);
        finalLucideIcons.push(icon);
      }
    }
  }

  // Add mapped icons (if not already present)
  for (const item of mappedToLucide) {
    // Always preserve the original alias if one existed
    const useAlias = item.alias || (item.originalName !== item.lucideName ? item.originalName : null);

    if (!seenLucideNames.has(item.lucideName)) {
      seenLucideNames.add(item.lucideName);
      finalLucideIcons.push({
        name: item.lucideName,
        alias: useAlias,
      });
    } else {
      // Name already in lucide import. If original had an alias, we need to
      // check if the existing entry matches. If the existing entry doesn't have
      // the alias but the original does, we need to update it.
      if (useAlias) {
        const existing = finalLucideIcons.find(i => i.name === item.lucideName);
        if (existing && !existing.alias) {
          existing.alias = useAlias;
        }
      }
      // If no alias needed, just skip - it's already imported
    }
  }

  // === Build the new import statements ===

  // 1. Build the NEW phosphor import (only unmapped icons)
  let newPhosphorImport = '';
  if (unmapped.length > 0) {
    const specs = unmapped.map(s => s.alias ? `${s.name} as ${s.alias}` : s.name);
    newPhosphorImport = `import { ${specs.join(', ')} } from '@phosphor-icons/react'`;
  }

  // 2. Build the NEW lucide import
  let newLucideImport = '';
  if (finalLucideIcons.length > 0) {
    const specs = finalLucideIcons.map(s => s.alias ? `${s.name} as ${s.alias}` : s.name);
    newLucideImport = `import { ${specs.join(', ')} } from 'lucide-react'`;
  }

  // === Replace in file ===

  // Remove weight props on JSX elements that reference phosphor icons now mapped to lucide
  // We don't know which props belong to which icons without AST, but we can do a simple
  // replacement for common patterns like `weight="fill"`, `weight="duotone"`, etc.
  // Actually, we'll do this as a separate cleanup step.
  
  // For each phosphor icon that's being migrated, remove `weight=` props from JSX usage
  // This is a rough heuristic - look for patterns like `weight="fill"` on migrated icons
  for (const item of mappedToLucide) {
    // Remove weight prop from <IconName ... /> usage
    // Match `weight="xxx"` or `weight={'xxx'}` or `weight={xxx}`
    // This is approximate but catches most cases
    const weightRe = /\s+weight\s*=\s*(?:"[^"]*"|'[^']*'|\{[^}]*\})/g;
    // We'll do a global cleanup at the end instead
  }

  // Now do the actual replacements in the content

  // Remove all phosphor import statements (we'll rebuild them)
  for (const imp of phosphorImports) {
    content = content.replace(imp.fullMatch, '');
  }

  // Remove all existing lucide import statements
  if (existingLucide.fullMatch) {
    content = content.replace(existingLucide.fullMatch, '');
  }

  // Clean up extra blank lines caused by import removal
  content = content.replace(/\n{3,}/g, '\n\n');

  // Determine where to place the new imports
  // Find the first import statement in the file to use as anchor
  const firstImportMatch = content.match(/^import\s/m);
  let insertPos = 0;
  if (firstImportMatch) {
    insertPos = firstImportMatch.index;
  }

  // Build the new import block
  const importLines = [];
  if (newLucideImport) importLines.push(newLucideImport);
  if (newPhosphorImport) importLines.push(newPhosphorImport);

  if (importLines.length === 0 && phosphorImports.length > 0 && allPhosphorSpecifiers.length === mappedToLucide.length) {
    // All icons were migrated, no imports needed
    // Remove the empty lines where imports were
    // Already handled above
  }

  // Build the new import block
  let newImportBlock = importLines.join('\n');
  if (newImportBlock) newImportBlock += '\n';

  // If there were no existing lucide imports and no remaining phosphor imports,
  // we just remove them and put nothing
  // Insert the new imports at the top
  if (newImportBlock) {
    content = content.slice(0, insertPos) + newImportBlock + content.slice(insertPos);
  }

  // Clean up extra newlines
  content = content.replace(/\n{3,}/g, '\n\n');
  content = content.replace(/^\n+/, '');
  content = content.trimStart();

  // === Remove weight props for migrated icons ===
  // For each migrated icon name, remove weight= props from JSX tags
  // Only if the icon is now using lucide (which doesn't support weight)
  for (const item of mappedToLucide) {
    const iconName = item.alias || item.originalName;
    // Match weight prop in JSX: <IconName ... weight="..." ... />
    const tagRe = new RegExp(`(<${iconName}[^>]*?)\\s+weight\\s*=\\s*(?:"[^"]*"|'[^']*'|\\{[^}]*\\})([^>]*>)`, 'gs');
    content = content.replace(tagRe, '$1$2');
    // Also match self-closing
    const selfClosingRe = new RegExp(`(<${iconName}[^>]*?)\\s+weight\\s*=\\s*(?:"[^"]*"|'[^']*'|\\{[^}]*\\})(\\s*\/?>)`, 'gs');
    content = content.replace(selfClosingRe, '$1$2');
  }

  // Extra cleanup for weight props that may be on any element (broader pattern)
  // Only for elements whose className indicates an icon or specific tag names
  // Actually let's be more targeted:
  // Remove weight="xxx" from any JSX element since weight is a phosphor-only prop
  // But this could be too aggressive. Let's just do it for the migrated icons.

  // Additional cleanup: remove duplicate empty lines
  content = content.replace(/^\s*[\r\n]/gm, match => match.includes('\n') ? '\n' : '');
  content = content.replace(/\n{3,}/g, '\n\n');

  // === Rename JSX usage for non-aliased renames ===
  // If an icon had no alias but its name changed (e.g. MarkdownLogo → FileText),
  // rename all occurrences in JSX to the new lucide name.
  // Only rename identifiers that look like component names (PascalCase, used as JSX tags).
  for (const item of mappedToLucide) {
    if (!item.alias && item.originalName !== item.lucideName) {
      const oldName = item.originalName;
      const newName = item.lucideName;
      // Match as a JSX tag: <OldName ...> or <OldName ... />
      // Also match as component reference: { OldName } or {OldName} or variable OldName
      const tagOpenRe = new RegExp(`<${oldName}([\\s>\\/])`, 'g');
      content = content.replace(tagOpenRe, `<${newName}$1`);
      const tagCloseRe = new RegExp(`<\\/${oldName}>`, 'g');
      content = content.replace(tagCloseRe, `</${newName}>`);
      // Also match as a value in JSX like `Icon: OldName` or `{ OldName }` or as variable reference
      // Be careful not to rename import specifiers (they've already been replaced)
      const varRefRe = new RegExp(`(?<![\\w\\d_])${oldName}(?![\\w\\d_])`, 'g');
      // But only in non-import contexts - we already removed imports, so this is safe
      content = content.replace(varRefRe, newName);
    }
  }

  // Write the file if changed
  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf-8');
    return {
      file: filePath,
      original,
      new: content,
      mapped: mappedToLucide.map(m => `${m.originalName}→${m.lucideName}${m.alias ? ` as ${m.alias}` : ''}`),
      unmapped: unmapped.map(m => m.alias ? `${m.name} as ${m.alias}` : m.name),
      fullyMigrated: unmapped.length === 0,
    };
  }

  return null;
}

// === Main ===
function main() {
  const allFiles = [];

  // Collect all .ts and .tsx files
  function collect(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === 'node_modules' || entry.name === '.next') continue;
        collect(fullPath);
      } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx'))) {
        allFiles.push(fullPath);
      }
    }
  }

  collect(WEB_ROOT);

  const results = [];
  for (const file of allFiles) {
    try {
      const result = processFile(file);
      if (result) results.push(result);
    } catch (err) {
      console.error(`Error processing ${file}:`, err.message);
    }
  }

  // Summary
  const fullyMigrated = results.filter(r => r.fullyMigrated);
  const partiallyMigrated = results.filter(r => !r.fullyMigrated);

  console.log('\n=== MIGRATION COMPLETE ===');
  console.log(`Total files processed: ${results.length}`);
  console.log(`Fully migrated (all phosphor icons mapped): ${fullyMigrated.length}`);
  console.log(`Partially migrated (some phosphor icons left): ${partiallyMigrated.length}`);
  console.log(`Total phosphor imports removed: ${results.filter(r => r.new.indexOf('@phosphor-icons/react') === -1).length} files`);

  if (partiallyMigrated.length > 0) {
    console.log('\n=== PARTIALLY MIGRATED FILES (unmapped icons remain) ===');
    for (const r of partiallyMigrated) {
      console.log(`\n${r.file}`);
      console.log(`  Unmapped: ${r.unmapped.join(', ')}`);
    }
  }
}

main();
