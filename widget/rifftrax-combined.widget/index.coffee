command: "printf '%s\n---SPLIT---\n%s' \"$(cat ~/.rifftrax_now_playing.txt 2>/dev/null)\" \"$(cat ~/.rifftrax_trivia.txt 2>/dev/null)\""

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

  .divider
    border: none
    border-top: 1px solid rgba(255,255,255,0.15)
    margin: 12px 0
    display: none

    &.visible
      display: block

  .ticker-wrap
    overflow: hidden
    width: 100%

  .ticker
    display: inline-block
    white-space: nowrap
    padding-left: 100%
    animation: marquee 60s linear infinite
    will-change: transform

  @keyframes marquee
    from
      transform: translateX(0)
    to
      transform: translateX(-100%)

  .trivia-section
    display: none

    &.visible
      display: block
"""

render: (output) ->
  parts = output.split('\n---SPLIT---\n')
  title  = (parts[0] or '').trim()
  trivia = (parts[1] or '').trim()
  """
  <div class='now-playing-section'>
    <div class='label'>📽 Now Riffing</div>
    <div class='title'>#{title}</div>
  </div>
  <hr class='divider'>
  <div class='trivia-section'>
    <div class='label'>🎬 Trivia</div>
    <div class='ticker-wrap'>
      <span class='ticker'>#{trivia}</span>
    </div>
  </div>
  """

update: (output, domEl) ->
  parts  = output.split('\n---SPLIT---\n')
  title  = (parts[0] or '').trim()
  trivia = (parts[1] or '').trim()
  $el = $(domEl)

  $el.find('.title').text(title)

  $triviaSection = $el.find('.trivia-section')
  $ticker = $el.find('.ticker')
  if trivia and $ticker.text() != trivia
    $ticker.text(trivia)

  $triviaSection.toggleClass('visible', !!trivia)
  $el.find('.divider').toggleClass('visible', !!(title and trivia))

  if title or trivia
    $el.find('.now-playing-section').toggle(!!title)
    $el.addClass('visible')
  else
    $el.removeClass('visible')
