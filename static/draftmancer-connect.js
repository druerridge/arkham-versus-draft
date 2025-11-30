// Socket.IO will be available globally from the script tag in HTML
// import { io } from "socketio";

export const GAME_MODE = {
    DRAFT: "DRAFT",
}

export function generateDraftmancerSession(CubeFile, tabToOpen, metadata, gameMode = GAME_MODE.DRAFT) {
    
    const Domain = "https://draftmancer.com";

    // Generate unique user ID and session ID
    const BotID = "ArkhamTDBot_" + crypto.randomUUID();
    const SessionID = "ArkhamTD_" + crypto.randomUUID();
    
    // Calculate max players based on sufficient cards in each category
    // Read actual values from the form inputs
    const investigatorsPerPlayer = parseInt(document.getElementById('investigatorsPerPack')?.value || 3);
    const weaknessesPerPlayer = parseInt(document.getElementById('basicWeaknessesPerPack')?.value || 3);
    const playerCardsPerPack = parseInt(document.getElementById('playerCardsPerPack')?.value || 15);
    const playerCardPacksPerPlayer = parseInt(document.getElementById('playerCardPacksPerPlayer')?.value || 3);
    
    // Calculate total player cards needed per player
    const playerCardsPerPlayer = playerCardsPerPack * playerCardPacksPerPlayer;
    
    const maxPlayersByInvestigators = Math.floor(metadata.investigatorsCount / investigatorsPerPlayer);
    const maxPlayersByWeaknesses = Math.floor(metadata.basicWeaknessesCount / weaknessesPerPlayer);
    const maxPlayersByPlayerCards = Math.floor(metadata.playerCardsCount / playerCardsPerPlayer);
    
    // The maximum players is limited by whichever category has the least cards
    const maxSupportedPlayers = Math.min(maxPlayersByInvestigators, maxPlayersByWeaknesses, maxPlayersByPlayerCards);
    
    // Set number of bots based on draft type
    let numBots;
    if (metadata.draftType === 'human') {
        numBots = 0;  // No bots for human drafts
    } else {
        numBots = Math.min(maxSupportedPlayers - 1, 7);  // Default bot draft behavior
    }
    
    const query = {
        userID: BotID,
        userName: "ArkhamTD Bot",
        sessionSettings: JSON.stringify({bots: numBots, maxTimer: 0}),
        sessionID: SessionID,
    };

    // Use the global io object loaded from CDN
    const socket = io(Domain, {
        query,
        transports: ["websocket"], // This is necessary to bypass CORS
    });

    // One of the message received by the client immediately on connection will
    // give you the current session owner. If the session was just created,
    // it should be our bot.
    socket.once("sessionOwner", (ownerID) => {
        if (ownerID !== BotID) {
            console.error("Not the owner!");
            tabToOpen.close();
            socket.disconnect();
            return;
        }

        socket.emit("parseCustomCardList", CubeFile, (res) => {
            if (res.code < 0) {
                console.error(res);
                tabToOpen.close();
                socket.disconnect();
            } else {
                // Deemmed this unnecessary - makes mixing bots + humans harder, and doesn't support >2 teams
                // if (metadata.draftType === 'human') {
                //     socket.emit("teamDraft", true, (res) => {
                //         if (res.code < 0) {
                //             console.error("Error setting team draft:", res);
                //         } else {
                //             console.log("Team draft mode enabled for human draft.");
                //         }
                //     });
                // }    
                
                // Automatically disconnect bot once the human user has joined the session
                    socket.once("sessionUsers", () => {
                        console.log("Draftmancer session started successfully.");
                        socket.disconnect();
                    });
                    // Open Draftmancer in specified tab
                    tabToOpen.location.href = `${Domain}/?session=${SessionID}`;
                // if (metadata.cubeId) {
                //     request(`/api/draftStarted`,null,startDraftOnCompletion,startDraftOnCompletion,'POST');
                // } else {
                //     startDraftOnCompletion(null);
                // }
            }
        });
    });
}