

close all
clear all
clc

global sid
serialAddress = '/dev/ttyACM1';

% stimList = {'medias/MF3D_Coo0.25_Haz0_Hel0_Gaz0_Gel0_RGBA.png'
%             'medias/MF3D_Fear0.25_Haz0_Hel0_Gaz0_Gel0_RGBA.png'
%             'medias/MF3D_Neutral1.00_Haz0_Hel0_Gaz0_Gel0_RGBA.png'
%             'medias/MF3D_Tongue0.25_Haz0_Hel0_Gaz0_Gel0_RGBA.png'
%             'medias/MF3D_Yawn0.25_Haz0_Hel0_Gaz0_Gel0_RGBA.png'};

stimList = {'medias/food_almonds.png'
    'medias/food_apple.png'
    'medias/food_avocado.png'
    'medias/food_banana.png'
    'medias/food_blackberry.png'
    'medias/food_carrots.png'
    'medias/food_cauliflower.png'
    'medias/food_cherry.png'
    'medias/food_corn.png'
%     'medias/food_cucumber.png'
%     'medias/food_eggplants.png'
    'medias/food_greenonion.png'
%     'medias/food_kiwi.png'
    'medias/food_onion.png'
    'medias/food_orange.png'
%     'medias/food_peanut.png'
    'medias/food_pepper.png'
    'medias/food_potato.png'
    'medias/food_salad.png'
    'medias/food_strawberry.png'
    'medias/food_tomato.png'};

stimNum = length(stimList);
        
screenNum = 1;
screenRes = [1920, 1080];
bg = 128;
% simSize = [3840,2160];

charucoDur = 1;
charucoPostGap = 1;

targetNumber = 20;
targetITIMin = 0.25;
targetITIMax = 0.75;
targetTargetMin = 1.0;
targetTargetMax = 1.0;
targetSpeed = 200;

% targetSizePix = 600;
targetSizePix = 200;
targetSizePixFreq = 0.5;
targetGapPix = 150;
targetRangeX = 800;

arucoSizePix = 12*15;
arucoGapPix = 2*arucoSizePix;

[tgPosMatX, tgPosMatY] = meshgrid(linspace(targetGapPix,screenRes(1)-targetGapPix,targetNumber),...
                                  linspace(targetGapPix,screenRes(2)-targetGapPix,targetNumber));
tgOrder = randperm(targetNumber^2);
tgPosMatX = tgPosMatX(tgOrder);
tgPosMatY = tgPosMatY(tgOrder);


% Connect to arduino
try
    serial_conn = instrfind;
    for cc=1:length(serial_conn)
        if strcmp(serial_conn(cc).Status,'open')
            fclose(serial_conn(cc));
        end
    end
    sid = serial(serialAddress, 'BaudRate', 9600, 'Timeout', 0.1, 'Terminator','');
    fopen(sid);
    while sid.BytesAvailable
        fread(sid);
    end
catch
    sid = -1;
    disp('Failed')
end


% Setup window
Screen('Preference', 'SkipSyncTests', 1);
KbName('UnifyKeyNames');
Screen('Preference', 'VisualDebugLevel', 0);
win = Screen('OpenWindow', screenNum, 128, [0,0,screenRes]);
Screen('BlendFunction', win, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);


HideCursor;
ListenChar(2);

% Load aruco markers
markersNumber = 4;
im_markers = cell(markersNumber,1);
for mm=1:markersNumber
    im_markers{mm} = Screen('MakeTexture', win, imread(sprintf('medias/aruco%i.png',mm-1)));
end
im_markers_rect = Screen('Rect', im_markers{1});


% Load charuco board
im_board = Screen('MakeTexture', win, imread('medias/charuco2.png'));
im_board_rect = Screen('Rect', im_board);


%% First display charuco board
board_draw_rect = [ 0.5*(screenRes(1)-im_board_rect(3)),...
                    0.5*(screenRes(2)-im_board_rect(4)),...
                    0.5*(screenRes(1)+im_board_rect(3)),...
                    0.5*(screenRes(2)+im_board_rect(4)) ];

Screen('FillRect', win, bg);
Screen('Drawtexture', win, im_board, [], board_draw_rect);
vbl = Screen('Flip', win, 0);
serialSend('on()');

KbWait;

Screen('FillRect', win, bg);
vbl = Screen('Flip', win, vbl+charucoDur-0.5/60);
serialSend('off()');


%% Then display calibration targets
for target=1:targetNumber
    durITI = targetITIMin+rand*(targetITIMax-targetITIMin);
    durTarget = targetTargetMin+rand*(targetTargetMax-targetTargetMin);
    currStim = ceil(stimNum*rand);
    tgDir = rand*2*pi;
    startPos = [targetRangeX*(rand-0.5),0];
%     tgPos = -0.5*targetSpeed*durTarget.*[cos(tgDir),sin(tgDir)]+0.5*screenRes;
%     [tgPosMatX(target),tgPosMatY(target)];
%     randPhase = rand*2*pi;
    
    Screen('FillRect', win, bg);
    vbl = Screen('Flip', win, vbl+durITI-0.5/60);
    serialSend('on()');
    
    [I,~,alpha] = imread(stimList{currStim});
    I(:,:,4) = alpha;
    stimTex = Screen('MakeTexture', win, I);
    stimTex_rect = Screen('Rect', stimTex);
    disp(currStim)
    disp(stimTex_rect)
    stimTex_rectScaled = stimTex_rect(3:4)*targetSizePix./max(stimTex_rect);
    
    timeStart = vbl;
    while GetSecs<(timeStart+durTarget)
        tgPos = -0.5*targetSpeed*durTarget.*[cos(tgDir),sin(tgDir)]+0.5*screenRes + ...
            (GetSecs-timeStart).*targetSpeed.*[cos(tgDir),sin(tgDir)] + ...
            startPos;
        
        Screen('FillRect', win, bg);
        for mm=1:markersNumber
            arucoCenter = tgPos + arucoGapPix * [fix(mm/2.5)-0.5, rem(mm,2)-0.5];
            Screen('Drawtexture', win, im_markers{mm}, [],...
                [arucoCenter-0.5*arucoSizePix,arucoCenter+0.5*arucoSizePix], [], 0);
        end
        Screen('Drawtexture', win, stimTex, [],...
                [tgPos-0.5*stimTex_rectScaled,tgPos+0.5*stimTex_rectScaled]);
        vbl = Screen('Flip', win, vbl+0.5/60);
        checkKB;
    end
    
    Screen('FillRect', win, bg);
    vbl = Screen('Flip', win, vbl+0.5/60);
    serialSend('off()');
    
end


cleanup;



function serialSend(str)
    global sid
    if ~(sid==-1)
        fwrite(sid, sprintf('%s\r\f',str));
        % Timeout seems broken, always waits for 1 sec regardless
%         resp = fscanf(sid,'%s\r>>> ');
%         fprintf([resp,'\n']);
    else
        fprintf('No serial connection\n');
    end
end

function checkKB
    [~, ~, keyCode] = KbCheck;
    if keyCode(KbName('ESCAPE'))
        cleanup
    end
end

function cleanup
    global sid
    Screen('CloseAll');
    if ~(sid==-1)
        serialSend('off()');
        fclose(sid);
    end
    ListenChar(0);
end

