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
    const maxSupportedPlayers = Math.floor( (metadata.investigatorsCount + metadata.basicWeaknessesCount + metadata.playerCardsCount) / (3 + 3 + 45) )
    const numBots = Math.min(maxSupportedPlayers - 1, 7) ;
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
                function startDraftOnCompletion(responseData) {
                    // Automatically disconnect bot once the human user has joined the session
                    socket.once("sessionUsers", () => {
                        console.log("Draftmancer session started successfully.");
                        socket.disconnect();
                    });
                    // Open Draftmancer in specified tab
                    tabToOpen.location.href = `${Domain}/?session=${SessionID}`;
                }
                // if (metadata.cubeId) {
                //     request(`/api/draftStarted`,null,startDraftOnCompletion,startDraftOnCompletion,'POST');
                // } else {
                //     startDraftOnCompletion(null);
                // }
                startDraftOnCompletion(null);
            }
        });
    });
}