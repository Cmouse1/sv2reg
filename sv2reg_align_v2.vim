" sv2reg_align_v2.vim — 纯 Vim 版 sv2reg 端口对齐
"
" 功能：自动对齐 .port_name / (signal) / , / // 四列
" 用法：:call Sv2RegAlignV2() 或可视模式 :'<,'>call Sv2RegAlignV2()

function! Sv2RegAlignV2(...) range
    if a:0 >= 2
        let l:start = a:1
        let l:end   = a:2
    else
        let l:start = a:firstline
        let l:end   = a:lastline
    endif

    let l:entries = []
    let l:max_name = 0
    let l:max_signal = 0

    let l:lnum = l:start
    while l:lnum <= l:end
        let l:line = getline(l:lnum)
        if l:line !~# '^\s*\.\w'
            let l:lnum += 1
            continue
        endif

        let l:trimmed = substitute(l:line, '^\s\+', '', '')
        let l:c_idx = stridx(l:trimmed, '//')
        if l:c_idx >= 0
            let l:port_part = strpart(l:trimmed, 0, l:c_idx)
            let l:comment   = strpart(l:trimmed, l:c_idx)
        else
            let l:port_part = l:trimmed
            let l:comment   = ''
        endif
        let l:port_part = substitute(l:port_part, '\s\+$', '', '')

        let l:port_name = matchstr(l:port_part, '^\.\w\+')
        let l:tail = strpart(l:port_part, strlen(l:port_name))
        let l:tail = substitute(l:tail, '^\s\+', '', '')

        let l:signal_block = ''
        if strlen(l:tail) > 0 && l:tail[0] == '('
            let l:close_idx = stridx(l:tail, ')')
            if l:close_idx >= 0
                let l:signal_block = strpart(l:tail, 0, l:close_idx + 1)
                let l:tail = strpart(l:tail, l:close_idx + 1)
                let l:tail = substitute(l:tail, '^\s\+', '', '')
            endif
        endif

        let l:comma = ''
        if strlen(l:tail) > 0 && l:tail[0] == ','
            let l:comma = ','
        endif

        if strlen(l:port_name) > l:max_name
            let l:max_name = strlen(l:port_name)
        endif
        if strlen(l:signal_block) > l:max_signal
            let l:max_signal = strlen(l:signal_block)
        endif

        call add(l:entries, [l:lnum, l:port_name, l:signal_block, l:comma, l:comment])
        let l:lnum += 1
    endwhile

    if empty(l:entries)
        echo 'Sv2RegAlignV2: no port lines found'
        return
    endif

    for [l:lnum, l:port_name, l:signal_block, l:comma, l:comment] in l:entries
        let l:new = ' ' . l:port_name
        let l:name_pad = l:max_name - strlen(l:port_name)
        if l:name_pad > 0
            let l:new .= repeat(' ', l:name_pad)
        endif
        let l:new .= '  '
        if !empty(l:signal_block)
            let l:new .= l:signal_block
            let l:sig_pad = l:max_signal - strlen(l:signal_block)
            if l:sig_pad > 0
                let l:new .= repeat(' ', l:sig_pad)
            endif
        elseif l:max_signal > 0
            let l:new .= repeat(' ', l:max_signal)
        endif
        let l:new .= '  '
        if !empty(l:comma)
            let l:new .= l:comma
        else
            let l:new .= ' '
        endif
        if !empty(l:comment)
            let l:new .= '  ' . l:comment
        endif
        call setline(l:lnum, l:new)
    endfor

    echo printf('Sv2RegAlignV2: aligned %d port lines', len(l:entries))
endfunction

command! -range Sv2RegAlignV2 <line1>,<line2>call Sv2RegAlignV2()
