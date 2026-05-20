" ============================================================================
" sv2reg_align.vim  —  Auto-align sv2reg-format SV port declarations
"
" 调用同目录下的 sv2reg_align.py 完成对齐，支持 range 和 whole-file 模式。
"
" 用法：
"   :call Sv2RegAlign()              " 全文件
"   :10,30call Sv2RegAlign()         " 指定范围
"   可视模式选中 -> :'<,'>call Sv2RegAlign()
"
" 前提：同目录下需有 sv2reg_align.py
" ============================================================================

function! Sv2RegAlign(...) range
    " Find the Python script (same directory as this vim file, or cwd)
    let l:script = expand('<sfile>:p:h') . '/sv2reg_align.py'
    if !filereadable(l:script)
        let l:script = 'sv2reg_align.py'
    endif

    " Determine range
    if a:0 >= 2
        let l:start = a:1
        let l:end   = a:2
    else
        let l:start = a:firstline
        let l:end   = a:lastline
    endif

    " Save range lines to temp file
    let l:tmp = tempname() . '.sv'
    call writefile(getline(l:start, l:end), l:tmp)

    " Run Python aligner
    let l:out = system('python3 ' . shellescape(l:script) . ' --inplace ' . shellescape(l:tmp))
    if v:shell_error != 0
        echoerr 'Sv2RegAlign: python3 failed — ' . l:out
        return
    endif

    " Read back aligned lines
    let l:aligned = readfile(l:tmp)
    call delete(l:tmp)

    if empty(l:aligned) || l:aligned == getline(l:start, l:end)
        echo 'Sv2RegAlign: no changes needed'
        return
    endif

    " Replace lines in buffer
    let l:idx = l:start
    for l:line in l:aligned
        call setline(l:idx, l:line)
        let l:idx += 1
    endfor

    " Delete extra lines if aligned has fewer lines
    while l:idx <= l:end
        execute l:idx . 'delete'
        let l:end -= 1
    endwhile

    echo printf('Sv2RegAlign: aligned %d lines', len(l:aligned))
endfunction

command! -range Sv2RegAlign <line1>,<line2>call Sv2RegAlign()
