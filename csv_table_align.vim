" csv_table_align.vim — Align comma-separated table columns
" ============================================================
" Core function:
"   CsvTableAlign(start_line, end_line)
"     -> Aligns columns for the given line range.
"
" Convenience command:
"   :CsvTableAlign           -> :'<,'>call CsvTableAlignRange()
"
" Algorithm:
"   Pass 1: split each line by comma, trim each field, track max width per column.
"   Pass 2: col_width = max_width>0 ? max_width+1 : 1
"   Pass 3: rebuild each line: text + space-padding to col_width + ',' + ...

" ---------------------------------------------------------------------------
" CsvTableAlign(start_line, end_line)
" ---------------------------------------------------------------------------
function! CsvTableAlign(start_line, end_line) abort
  let l:lines = getline(a:start_line, a:end_line)
  if empty(l:lines)
    return
  endif

  " Pass 1: split & trim; collect trimmed columns per row.
  let l:rows = []
  let l:num_cols = 0
  for l:raw in l:lines
    let l:parts = split(l:raw, ',', 1)  " keepempty=1
    let l:cols = map(l:parts, {_, v -> substitute(substitute(v, '^\s\+', '', ''), '\s\+$', '', '')})
    call add(l:rows, l:cols)
    if len(l:cols) > l:num_cols
      let l:num_cols = len(l:cols)
    endif
  endfor

  " Normalize: ensure every row has the same number of columns.
  for l:row in l:rows
    while len(l:row) < l:num_cols
      call add(l:row, '')
    endwhile
  endfor

  " Pass 2: compute max text width per column.
  let l:max_width = repeat([0], l:num_cols)
  for l:row in l:rows
    for l:i in range(l:num_cols)
      let l:w = len(l:row[l:i])
      if l:w > l:max_width[l:i]
        let l:max_width[l:i] = l:w
      endif
    endfor
  endfor

  " Column display width = max_width + 1 (at least 1).
  let l:col_width = map(l:max_width, {_, v -> v > 0 ? v + 1 : 1})

  " Pass 3: rebuild each line with padding.
  " Format per column: text + pad_to_width + separator
  "   separator = ', ' for non-last columns, '' for last column
  let l:new_lines = []
  for l:row in l:rows
    let l:parts = []
    for l:i in range(l:num_cols)
      let l:text = l:row[l:i]
      let l:pad  = l:col_width[l:i] - len(l:text)
      if l:pad < 0
        let l:pad = 0
      endif
      if l:i == l:num_cols - 1
        call add(l:parts, l:text . repeat(' ', l:pad))
      else
        call add(l:parts, l:text . repeat(' ', l:pad) . ', ')
      endif
    endfor
    call add(l:new_lines, join(l:parts, ''))
  endfor

  " Replace the target range.
  call setline(a:start_line, l:new_lines)
endfunction

" ---------------------------------------------------------------------------
" CsvTableAlignRange — range wrapper
" ---------------------------------------------------------------------------
function! CsvTableAlignRange() range abort
  call CsvTableAlign(a:firstline, a:lastline)
endfunction

command! -range CsvTableAlign <line1>,<line2>call CsvTableAlignRange()

" ---------------------------------------------------------------------------
" CsvTableAlignPorts — auto-locate <MODULE_PORT_START> / <MODULE_PORT_END>
" ---------------------------------------------------------------------------
function! CsvTableAlignPorts() abort
  " Locate the start marker anywhere in the buffer.
  let l:start_marker = search('<MODULE_PORT_START>', 'w')
  if l:start_marker == 0
    echohl ErrorMsg | echo 'CsvTableAlignPorts: <MODULE_PORT_START> not found' | echohl None
    return
  endif
  " Locate the end marker from the start marker position.
  let l:end_marker = search('<MODULE_PORT_END>', 'W')
  if l:end_marker == 0
    echohl ErrorMsg | echo 'CsvTableAlignPorts: <MODULE_PORT_END> not found' | echohl None
    return
  endif
  " The table lines are between the two markers (exclusive).
  let l:s = l:start_marker + 1
  let l:e = l:end_marker - 1
  if l:s > l:e
    echohl WarningMsg | echo 'CsvTableAlignPorts: no lines between markers' | echohl None
    return
  endif
  call CsvTableAlign(l:s, l:e)
  echo 'CsvTableAlignPorts: aligned lines ' . l:s . '-' . l:e
endfunction

command! CsvTableAlignPorts call CsvTableAlignPorts()
