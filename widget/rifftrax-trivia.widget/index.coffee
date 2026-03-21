command: "cat ~/.rifftrax_trivia.txt 2>/dev/null"

refreshFrequency: 5000

style: """
  top: 160px
  left: 40px
  font-family: -apple-system, BlinkMacSystemFont, sans-serif
  color: white
  background: rgba(0,0,0,0.75)
  border-left: 4px solid #e50914
  border-radius: 4px
  padding: 15px 22px
  max-width: 525px
  overflow: hidden
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

  .ticker-wrap
    overflow: hidden
    width: 100%

  .ticker
    display: inline-block
    white-space: nowrap
    animation: marquee 45s linear infinite

  @keyframes marquee
    from
      transform: translateX(100vw)
    to
      transform: translateX(-100vw)
"""

render: (output) -> """
  <div class='label'>🎬 Trivia</div>
  <div class='ticker-wrap'>
    <span class='ticker'>#{output.trim()}</span>
  </div>
"""

update: (output, domEl) ->
  trivia = output.trim()
  $el = $(domEl)

  if trivia
    $ticker = $el.find('.ticker')
    if $ticker.text() != trivia
      $ticker.text(trivia)
    $el.addClass('visible')
  else
    $el.removeClass('visible')
