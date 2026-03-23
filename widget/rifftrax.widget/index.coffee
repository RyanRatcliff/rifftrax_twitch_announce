command: "printf '%s\n---SPLIT---\n%s' \"$(cat ~/.rifftrax_now_playing.txt 2>/dev/null)\" \"$(stat -f '%Sm' -t 'Started %I:%M %p' ~/.rifftrax_now_playing.txt 2>/dev/null)\""

refreshFrequency: 5000

style: """
  top: 40px
  left: 40px
  font-family: -apple-system, BlinkMacSystemFont, sans-serif
  color: white
  background: rgba(0,0,0,0.75)
  border-left: 4px solid #e50914
  border-radius: 4px
  padding: 15px 22px
  max-width: 525px
  display: none

  &.visible
    display: block

  .label
    font-size: 13px
    font-weight: 600
    letter-spacing: 0.12em
    text-transform: uppercase
    color: #e50914
    margin-bottom: 6px

  .title
    font-size: 22px
    font-weight: 600
    line-height: 1.3

  .starttime
    font-size: 11px
    font-weight: 400
    color: rgba(255,255,255,0.45)
    margin-top: 5px
    letter-spacing: 0.04em
"""

render: (output) ->
  parts     = output.split('\n---SPLIT---\n')
  title     = (parts[0] or '').trim()
  starttime = (parts[1] or '').trim()
  """
  <div class='label'>📽 Now Riffing</div>
  <div class='title'>#{title}</div>
  <div class='starttime'>#{starttime}</div>
  """

update: (output, domEl) ->
  parts     = output.split('\n---SPLIT---\n')
  title     = (parts[0] or '').trim()
  starttime = (parts[1] or '').trim()
  if title
    $(domEl).addClass('visible')
    $(domEl).find('.title').text(title)
    $(domEl).find('.starttime').text(starttime)
  else
    $(domEl).removeClass('visible')
