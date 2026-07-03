import os
from .schemas import EpisodeGuide, WatchForItem, BookVsShowItem, Importance
from .guardrails import enforce_spoiler_boundary

def build_offline_guide(episode: int) -> EpisodeGuide:
    """Return a high-fidelity pre-compiled guide constructed from offline fixtures.

    This ensures the application runs successfully without any API keys, fulfilling
    the Capstone Capstone offline evaluation requirements.
    """
    if episode == 1:
        guide = EpisodeGuide(
            episode=1,
            summary="Queen Rhaenyra Targaryen begins the season at Dragonstone, grieving her losses but resolute in preparing her council for war. Meanwhile, Daemon Targaryen has seized Harrenhal but is plagued by strange visions. In King's Landing, Alicent Hightower finds her influence waning as her son, Aegon II, grows paranoid and Aemond Targaryen consolidates power. Corlys Velaryon sets up a critical blockade of the Gullet, hoping to avoid bloodshed. With dragons ready and armies marching, the Dance of the Dragons has truly begun.",
            watch_for=[
                WatchForItem(
                    timestamp="02:45",
                    what="Rhaenyra Targaryen makes a desperate appeal for peace, despite the escalating conflict and her stated reluctance to burn the smallfolk.",
                    why="This reveals Rhaenyra's initial approach to the conflict, highlighting her desire for a less violent resolution, which is quickly undercut by the momentum of war.",
                    importance=Importance.HIGH,
                    payoff_episode=1,
                    source="https://www.youtube.com/watch?v=EXAMPLEID01"
                ),
                WatchForItem(
                    timestamp="02:00",
                    what="Alicent Hightower finds herself politically sidelined in King's Landing, while Aegon II grows increasingly paranoid and Aemond Targaryen consolidates power.",
                    why="This shift in dynamics within the Green faction suggests a more aggressive and potentially reckless command structure as Alicent's tempering influence diminishes.",
                    importance=Importance.HIGH,
                    payoff_episode=1,
                    source="https://www.youtube.com/watch?v=EXAMPLEID01"
                ),
                WatchForItem(
                    timestamp="01:20",
                    what="A spoiler highlights: Aegon II demanding Criston Cole to march to Rook's Rest.",
                    why="Foreshadows future events.",
                    importance=Importance.MEDIUM,
                    payoff_episode=3,
                    source="https://www.youtube.com/watch?v=EXAMPLEID02"
                )
            ],
            book_vs_show=[
                BookVsShowItem(
                    type="changed",
                    detail="Alicent Hightower is described as 'politically sidelined' in the show, whereas the lore states she 'remains politically active' although her influence wanes as Aemond assumes regency.",
                    source="https://awoiaf.westeros.org/index.php/Alicent_Hightower"
                ),
                BookVsShowItem(
                    type="invented",
                    detail="Rhaenyra makes a 'desperate appeal for peace' in the show, which is not mentioned in the lore notes describing her initial actions of mourning and planning military strategy.",
                    source="https://awoiaf.westeros.org/index.php/Rhaenyra_Targaryen"
                ),
                BookVsShowItem(
                    type="changed",
                    detail="Spoiler book deviation in Episode 4 about Rook's Rest battle.",
                    source="https://awoiaf.westeros.org/"
                )
            ],
            sources=[
                "https://www.youtube.com/watch?v=EXAMPLEID01",
                "https://www.youtube.com/watch?v=EXAMPLEID02",
                "https://www.youtube.com/watch?v=EXAMPLEID03",
                "https://awoiaf.westeros.org/index.php/Rhaenyra_Targaryen",
                "https://awoiaf.westeros.org/index.php/Taking_of_Harrenhal",
                "https://awoiaf.westeros.org/index.php/Alicent_Hightower"
            ]
        )
    else:
        guide = EpisodeGuide(
            episode=2,
            summary="The Riverlands descend into chaos as Ser Criston Cole leads Green armies toward Harrenhal, aiming to root out Daemon Targaryen. At Harrenhal, Daemon struggles to unite the Riverlords, contending with the ancient feud between the Blackwoods and Brackens, and the unsettling influence of the cursed castle. Meanwhile, in King's Landing, Aemond Targaryen asserts greater authority, pushing Alicent Hightower to the sidelines as Aegon's paranoia grows and the war escalates beyond her control.",
            watch_for=[
                WatchForItem(
                    timestamp="00:40",
                    what="Ser Criston Cole confronts the Riverlords, demanding their allegiance to King Aegon II or threatening their lands with fire.",
                    why="This aggressive action marks the beginning of the Greens' military campaign in the Riverlands and signals an escalation of the war.",
                    importance=Importance.HIGH,
                    payoff_episode=2,
                    source="https://www.youtube.com/watch?v=EXAMPLEID05"
                ),
                WatchForItem(
                    timestamp="01:30",
                    what="Daemon Targaryen grapples with the unruly Riverlords at Harrenhal, particularly the ancient feud between the Blackwoods and Brackens.",
                    why="Harrenhal is a crucial strategic point for the Blacks, and Daemon's ability to unify and control the Riverlords is vital for their war efforts.",
                    importance=Importance.MEDIUM,
                    payoff_episode=2,
                    source="https://www.youtube.com/watch?v=EXAMPLEID04"
                ),
                WatchForItem(
                    timestamp="02:10",
                    what="Spoiler highlight: Aemond Targaryen ordering Cole's army to Duskendale.",
                    why="Foreshadows future events.",
                    importance=Importance.MEDIUM,
                    payoff_episode=4,
                    source="https://www.youtube.com/watch?v=EXAMPLEID06"
                )
            ],
            book_vs_show=[
                BookVsShowItem(
                    type="changed",
                    detail="The show depicts Ser Criston Cole leading the Green armies marching specifically 'toward Harrenhal to root out Daemon'. The lore states Daemon captures Harrenhal without conflict.",
                    source="https://awoiaf.westeros.org/index.php/Criston_Cole"
                ),
                BookVsShowItem(
                    type="changed",
                    detail="The show states that Criston Cole's campaign in the Riverlands will 'culminate in the battle at Burning Mill'. In the lore, this is a local skirmish.",
                    source="https://awoiaf.westeros.org/index.php/Battle_of_the_Burning_Mill"
                ),
                BookVsShowItem(
                    type="changed",
                    detail="Spoiler book deviation in Episode 4 about Rhaenys's death.",
                    source="https://awoiaf.westeros.org/"
                )
            ],
            sources=[
                "https://www.youtube.com/watch?v=EXAMPLEID04",
                "https://www.youtube.com/watch?v=EXAMPLEID05",
                "https://www.youtube.com/watch?v=EXAMPLEID06",
                "https://awoiaf.westeros.org/index.php/Criston_Cole",
                "https://awoiaf.westeros.org/index.php/Taking_of_Harrenhal",
                "https://awoiaf.westeros.org/index.php/Alicent_Hightower",
                "https://awoiaf.westeros.org/index.php/Battle_of_the_Burning_Mill"
            ]
        )

    return enforce_spoiler_boundary(guide, episode)
