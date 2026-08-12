# Mobile Machines smoke

Manual viewport target: 390 CSS px.

Checks for the signed-in Machines directory:

- no horizontal page scroll;
- Machine card, transport status, and node metadata stay inside the card;
- Connect Direct / Edit Direct / Remove actions stay visible and tappable;
- tapping a Node with no saved Direct path and no online relay opens Direct configuration instead of only showing a transport error;
- Direct URL and access-key fields fit the viewport;
- Test and connect remains fully visible.

The regression screenshot that motivated this check showed the transport badge and Connect Direct action clipped beyond the right edge on a mobile viewport.
